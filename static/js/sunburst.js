// static/js/sunburst.js

document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('sunburst-viz');
    if (!container) return;

    // Fetch the data from our new API endpoint
    fetch('/api/sunburst')
        .then(response => response.json())
        .then(data => drawSunburst(data, container))
        .catch(error => {
            console.error('Error loading sunburst data:', error);
            container.innerHTML = '<p style="color: #dc2626; text-align: center; padding: 2rem;">Error loading visualization</p>';
        });
});

// JS script from https://observablehq.com/@d3/zoomable-sunburst

function drawSunburst(data, container) {
    container.innerHTML = '';

    const size = Math.min(container.clientWidth, 600);
    const width = size;
    const height = size;
    const radius = size / 5.97;

    const color = d3.scaleOrdinal()
        .domain(data.children.map(d => d.name))
        .range(["#a78bda", "#e17ba5", "#f2a679", "#c9b458", "#c5e17e", "#7ed99a", "#5fc9b0", "#7ab8d9"]);

    const hierarchy = d3.hierarchy(data)
        .sum(d => d.children ? (d.value || 0) : (d.value || 1));

    const root = d3.partition()
        .size([2 * Math.PI, hierarchy.height + 1])
        (hierarchy);

    root.each(d => d.current = d);

    const svg = d3.select(container).append("svg")
        .attr("viewBox", [-width / 2, -height / 2, width, height])
        .style("width", "100%")
        .style("height", "100%")
        .style("display", "block");

    const g = svg.append("g");

    const arc = d3.arc()
        .startAngle(d => d.x0)
        .endAngle(d => d.x1)
        .padAngle(d => Math.min((d.x1 - d.x0) / 2, 0.005))
        .padRadius(radius * 1.5)
        .innerRadius(d => d.y0 * radius)
        .outerRadius(d => Math.max(d.y0 * radius, d.y1 * radius - 1));

    const path = g.append("g")
        .selectAll("path")
        .data(root.descendants().slice(1))
        .join("path")
        .attr("fill", d => {
            let parent = d;
            while (parent.depth > 1) parent = parent.parent;
            return color(parent.data.name);
        })
        .attr("stroke", "#fff")
        .attr("stroke-width", 1)
        .attr("fill-opacity", d => arcVisible(d.current) ? (d.children ? 0.8 : 0.6) : 0)
        .attr("pointer-events", d => arcVisible(d.current) ? "auto" : "none")
        .attr("d", d => arc(d.current))
        .style("cursor", "pointer")
        .on("click", clicked);

    const format = d3.format(",d");
    path.append("title")
        .text(d => `${d.ancestors().map(d => d.data.name).reverse().join("/")}\n${format(d.value || 0)} tokens`);

    // Create hidden arcs for text paths (from GitHub code)
    const middleArcLine = d => {
        const halfPi = Math.PI / 2;
        const angles = [d.x0 - halfPi, d.x1 - halfPi];
        const r = ((d.y0 + d.y1) / 2) * radius;

        const middleAngle = (angles[1] + angles[0]) / 2;
        const invertDirection = middleAngle > 0 && middleAngle < Math.PI;
        if (invertDirection) { angles.reverse(); }

        const path = d3.path();
        path.arc(0, 0, r, angles[0], angles[1], invertDirection);
        return path.toString();
    };

    // Truncates a label to the character count that actually fits its arc's
    // real pixel length. SVG <textPath> has no line-wrap, so truncation-to-fit
    // (same idea as renderTitle's word-wrap, single-line version) is the
    // standard alternative to hiding text outright or letting it overflow
    // into a neighboring wedge.
    function fitArcText(name, coords) {
        const CHAR_SPACE = 4.5; 
        
        const deltaAngle = coords.x1 - coords.x0;
        const r = ((coords.y0 + coords.y1) / 2) * radius;
        const perimeter = r * deltaAngle;
        
        const maxChars = Math.floor(perimeter / CHAR_SPACE);
        
        if (name.length <= maxChars) return name;
        if (maxChars < 4) return '';   // truly too narrow for even "…" to help
        return name.substring(0, maxChars - 1) + '…';
    }

    // Create hidden arcs
    g.append("g")
        .selectAll("path")
        .data(root.descendants().slice(1))
        .join("path")
        .attr("class", "hidden-arc")
        .attr("fill", "none")
        .attr("id", (d, i) => `hiddenArc${i}`)
        .attr("d", d => middleArcLine(d.current))
        .style("display", "none");

    // Create curved text labels
    const label = g.append("g")
        .attr("pointer-events", "none")
        .style("user-select", "none")
        .selectAll("g")
        .data(root.descendants().slice(1))
        .join("g")
        .attr("opacity", d => arcVisible(d.current) ? 1 : 0);   // CHANGED — no longer gated by textFits; fitArcText handles overflow instead

    // Actual text
    label.append("text")
        .attr("text-anchor", "middle")
        .style("pointer-events", "none")
        .append("textPath")
        .attr("startOffset", "50%")
        .attr("xlink:href", (d, i) => `#hiddenArc${i}`)
        .text(d => fitArcText(d.data.name, d.current))   // CHANGED — truncate instead of showing raw name
        .style("fill", "#1d3557")
        .style("font-size", "6.8px")
        .style("font-weight", "200");

    const parent = g.append("circle")
        .datum(root)
        .attr("r", radius)
        .attr("fill", "none")
        .attr("pointer-events", "all")
        .on("click", clicked)
        .style("cursor", "pointer");

    // Renders (possibly multi-line) title text centered inside the donut hole.
    // Wraps on word boundaries rather than shrinking font size, so short
    // names ("Mechanisms") stay large and long ones ("Fast fashion...")
    // break into readable lines instead of overflowing the circle.
    function renderTitle(name, depth) {
        const fontSize = depth > 0 ? 16 : 20;
        const avgCharWidth = fontSize * 0.55; // rough estimate, same heuristic style as fitArcText
        const maxLineWidthPx = radius * 1.5;   // keep text within the donut hole, not touching the inner ring
        const maxCharsPerLine = Math.max(4, Math.floor(maxLineWidthPx / avgCharWidth));

        // Greedy word-wrap
        const words = name.split(' ');
        const lines = [];
        let current = '';
        words.forEach(word => {
            const attempt = current ? `${current} ${word}` : word;
            if (attempt.length > maxCharsPerLine && current) {
                lines.push(current);
                current = word;
            } else {
                current = attempt;
            }
        });
        if (current) lines.push(current);

        // Cap total lines so text doesn't overflow vertically past the circle's diameter
        const lineHeight = fontSize * 1.2;
        const maxLines = Math.max(2, Math.floor((radius * 1.6) / lineHeight));
        if (lines.length > maxLines) {
            lines.length = maxLines;
            lines[maxLines - 1] = lines[maxLines - 1].replace(/\s*\S*$/, '') + '…';
        }

        title.selectAll('tspan').remove();
        title.style('font-size', `${fontSize}px`);

        const startY = -((lines.length - 1) * lineHeight) / 2;
        lines.forEach((line, i) => {
            title.append('tspan')
                .attr('x', 0)
                .attr('y', startY + i * lineHeight)
                .style('dominant-baseline', 'middle')
                .text(line);
        });
    }

    const title = g.append("text")
        .attr("text-anchor", "middle")
        .style("font-weight", "bold")
        .style("fill", "#1d3557")
        .style("pointer-events", "none");

    renderTitle("Mechanisms", 0);

    function clicked(event, p) {
        parent.datum(p.parent || root);

        root.each(d => d.target = {
            x0: Math.max(0, Math.min(1, (d.x0 - p.x0) / (p.x1 - p.x0))) * 2 * Math.PI,
            x1: Math.max(0, Math.min(1, (d.x1 - p.x0) / (p.x1 - p.x0))) * 2 * Math.PI,
            y0: Math.max(0, d.y0 - p.depth),
            y1: Math.max(0, d.y1 - p.depth)
        });

        const t = g.transition().duration(750);

        // 1. Update the colored wedges
        path.transition(t)
            .tween("data", d => {
                const i = d3.interpolate(d.current, d.target);
                return t => d.current = i(t);
            })
            .filter(function(d) {
                return +this.getAttribute("fill-opacity") || arcVisible(d.target);
            })
            .attr("fill-opacity", d => arcVisible(d.target) ? (d.children ? 0.8 : 0.6) : 0)
            .attr("pointer-events", d => arcVisible(d.target) ? "auto" : "none")
            .attrTween("d", d => () => arc(d.current));

        // 2. Update the hidden arcs (for text) using the SAME d.current
        // We must select the hidden arcs and update their 'd' attribute 
        // in the same transition to ensure they move with the wedges.
        g.selectAll(".hidden-arc")
            .transition(t)
            .attrTween("d", function(d) {
                // 'this' is the hidden arc path element
                // We use the same interpolation logic to ensure sync
                const i = d3.interpolate(d.current, d.target);
                return t => middleArcLine(i(t)); // Use the interpolated values directly
            });

        // 3. Update text visibility and content
        label.transition(t)
            .attr("opacity", d => arcVisible(d.target) ? 1 : 0);

        // Update the text content to fit the NEW target geometry
        // We do this after the transition starts so it uses the final positions
        label.select("textPath")
            .transition(t)
            .tween("text", function(d) {
                const targetText = fitArcText(d.data.name, d.target);
                const currentText = this.textContent;
                const i = d3.interpolateString(currentText, targetText);
                return t => this.textContent = i(t);
            });

        renderTitle(p.depth === 0 ? "Mechanisms" : p.data.name, p.depth);
    }

    function arcVisible(d) {
        return d.y1 <= 3 && d.y0 >= 1 && d.x1 > d.x0;
    }

}