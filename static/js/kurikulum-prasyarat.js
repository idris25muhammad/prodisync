(function () {
    const config = window.kurikulumConfig || {};
    const categoryColors = config.categoryColors || {};
    const connections = config.connections || [];

    function drawLines(focusId = null) {
        const svg = document.getElementById('connection-layer');
        const wrapper = document.getElementById('mainWrapper');

        if (!svg || !wrapper) return;

        svg.innerHTML = '';

        const wrapperRect = wrapper.getBoundingClientRect();
        const activeNodes = new Set();
        const activeLines = new Set();

        if (focusId) {
            wrapper.classList.add('is-active');
            activeNodes.add(focusId);

            connections.forEach((conn, index) => {
                if (conn.ids[0] === focusId) {
                    activeNodes.add(conn.ids[1]);
                    activeLines.add(index);
                } else if (conn.ids[1] === focusId) {
                    activeNodes.add(conn.ids[0]);
                    activeLines.add(index);
                }
            });
        } else {
            wrapper.classList.remove('is-active');
        }

        connections.forEach((conn, index) => {
            const startEl = document.getElementById(conn.ids[0]);
            const endEl = document.getElementById(conn.ids[1]);

            if (!startEl || !endEl) return;

            const isHighlighted = activeLines.has(index);
            const startRect = startEl.getBoundingClientRect();
            const endRect = endEl.getBoundingClientRect();
            const color = categoryColors[conn.cat] || '#64748b';

            const x1 = startRect.left + (startRect.width / 2) - wrapperRect.left;
            const y1 = startRect.bottom - wrapperRect.top;
            const x2 = endRect.left + (endRect.width / 2) - wrapperRect.left;
            const y2 = endRect.top - wrapperRect.top;

            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            const cpY = y1 + ((y2 - y1) / 2);
            const d = `M ${x1} ${y1} C ${x1} ${cpY}, ${x2} ${cpY}, ${x2} ${y2}`;

            path.setAttribute('d', d);
            path.setAttribute('class', `connector-line ${isHighlighted ? 'highlight' : ''}`);
            path.style.stroke = color;
            svg.appendChild(path);

            const diamond = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
            const size = 5;
            const points = `${x2},${y2 - size} ${x2 + size},${y2} ${x2},${y2 + size} ${x2 - size},${y2}`;

            diamond.setAttribute('points', points);
            diamond.setAttribute('class', `endpoint-diamond ${isHighlighted ? 'highlight' : ''}`);
            diamond.style.fill = color;
            svg.appendChild(diamond);
        });

        document.querySelectorAll('.course-box').forEach(box => {
            box.classList.toggle('highlight', activeNodes.has(box.id));
        });
    }

    function bindEvents() {
        document.querySelectorAll('.course-box').forEach(box => {
            box.addEventListener('click', function (e) {
                e.stopPropagation();
                if (!box.id) return;
                drawLines(box.id);
            });
        });

        document.addEventListener('click', function () {
            drawLines(null);
        });

        window.addEventListener('resize', function () {
            drawLines(null);
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        drawLines();
        bindEvents();
    });
})();