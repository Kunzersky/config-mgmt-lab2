"""Render dependency graphs as Graphviz DOT, SVG, and ASCII trees."""

import html
import shutil
import subprocess
from collections import defaultdict, deque
from pathlib import Path


def quote_dot_label(name):
    """Escape one package name as a quoted Graphviz identifier."""
    escaped = name.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def format_graphviz(graph):
    """Return a Graphviz DOT digraph description."""
    lines = ["digraph dependencies {", "    rankdir=LR;"]
    for name in graph:
        lines.append(f"    {quote_dot_label(name)};")
    for package, dependencies in graph.items():
        for dependency in dependencies:
            lines.append(
                f"    {quote_dot_label(package)} -> "
                f"{quote_dot_label(dependency)};"
            )
    lines.append("}")
    return "\n".join(lines)


def append_tree(graph, package, prefix, seen, active, lines):
    """Append one package's children to the ASCII tree recursively."""
    children = graph.get(package, [])
    for index, child in enumerate(children):
        is_last = index == len(children) - 1
        branch = "`-- " if is_last else "|-- "
        repeated = child in seen
        cycle = child in active
        suffix = " (cycle)" if cycle else " (already shown)" if repeated else ""
        lines.append(f"{prefix}{branch}{child}{suffix}")
        if repeated:
            continue
        seen.add(child)
        active.add(child)
        child_prefix = prefix + ("    " if is_last else "|   ")
        append_tree(graph, child, child_prefix, seen, active, lines)
        active.remove(child)


def format_ascii_tree(graph, root):
    """Return an ASCII tree without expanding repeated or cyclic nodes."""
    lines = [root]
    append_tree(graph, root, "", {root}, {root}, lines)
    return "\n".join(lines)


def node_positions(graph, box_width):
    """Place graph nodes in columns based on their BFS distance from root."""
    root = next(iter(graph))
    depth = {root: 0}
    pending = deque([root])
    while pending:
        package = pending.popleft()
        for dependency in graph[package]:
            if dependency not in depth:
                depth[dependency] = depth[package] + 1
                pending.append(dependency)

    columns = defaultdict(list)
    for package in graph:
        columns[depth[package]].append(package)
    positions = {}
    column_gap = box_width + 100
    for level, packages in columns.items():
        for row, package in enumerate(packages):
            positions[package] = (40 + level * column_gap, 40 + row * 88)
    return positions, columns, column_gap


def append_edges(elements, graph, positions, box_width):
    """Append SVG paths for graph edges."""
    for package, dependencies in graph.items():
        x, y = positions[package]
        for dependency in dependencies:
            target_x, target_y = positions[dependency]
            start_x = x + box_width if target_x > x else x
            end_x = target_x if target_x > x else target_x + box_width
            start_y = y + 22
            end_y = target_y + 22
            bend_x = (start_x + end_x) // 2
            elements.append(
                f'<path d="M {start_x} {start_y} C {bend_x} {start_y}, '
                f'{bend_x} {end_y}, {end_x} {end_y}" '
                'fill="none" stroke="#53636f" stroke-width="2" '
                'marker-end="url(#arrow)"/>'
            )


def append_nodes(elements, positions, box_width):
    """Append labeled SVG boxes for graph nodes."""
    for package, (x, y) in positions.items():
        label = html.escape(package)
        elements.append(
            f'<rect x="{x}" y="{y}" width="{box_width}" height="44" '
            'rx="3" fill="#ffffff" stroke="#1f6b63" stroke-width="2"/>'
        )
        elements.append(
            f'<text x="{x + box_width // 2}" y="{y + 28}" '
            'text-anchor="middle" font-family="sans-serif" font-size="15" '
            f'fill="#183c3a">{label}</text>'
        )


def save_svg_fallback(graph, output_path):
    """Write SVG with the built-in layout when Graphviz is unavailable."""
    if not graph:
        raise ValueError("Cannot render an empty dependency graph")
    names = list(graph)
    box_width = max(150, max(len(name) for name in names) * 9 + 24)
    positions, columns, column_gap = node_positions(graph, box_width)
    width = 80 + (max(columns) + 1) * column_gap
    height = 80 + max(len(items) for items in columns.values()) * 88
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}">',
        "<defs><marker id=\"arrow\" markerWidth=\"8\" markerHeight=\"8\" "
        "refX=\"7\" refY=\"3\" orient=\"auto\">"
        "<path d=\"M0,0 L0,6 L8,3 z\" fill=\"#53636f\"/>"
        "</marker></defs>",
        '<rect width="100%" height="100%" fill="#f7f8f5"/>',
    ]
    append_edges(elements, graph, positions, box_width)
    append_nodes(elements, positions, box_width)
    elements.append("</svg>")
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(elements), encoding="utf-8")


def save_svg(graph, output_path):
    """Save DOT and render SVG with Graphviz or the built-in fallback."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    dot_path = destination.with_suffix(".dot")
    dot_source = format_graphviz(graph)
    dot_path.write_text(dot_source, encoding="utf-8")
    executable = shutil.which("dot")
    if executable is None:
        save_svg_fallback(graph, destination)
        return dot_path
    try:
        result = subprocess.run(
            [executable, "-Tsvg"], input=dot_source, capture_output=True,
            text=True, check=True
        )
    except subprocess.CalledProcessError as error:
        raise ValueError(f"Graphviz failed: {error.stderr.strip()}") from error
    destination.write_text(result.stdout, encoding="utf-8")
    return dot_path