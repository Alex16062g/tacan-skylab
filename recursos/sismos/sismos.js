import * as i18n from '../../idiomas/i18n.js';
export async function agregarSismos(map, maplibregl) {
    const response = await fetch(new URL('./tacana.geojson', import.meta.url));
    if (!response.ok) throw new Error(i18n.t("no_se_pudo_cargar_la_capa_de_sismos_del_tacana"));
    const data = await response.json();
    if (!Object.hasOwn(HTMLElement.prototype, 'popover')) {
        await import('./vendor/popover.iife.min.js');
    }
    if (!('interestForElement' in HTMLButtonElement.prototype)) {
        await import('./vendor/interestfor.min.js');
    }
    const hints = [];
    const containers = [];
    const minimumZoom = 10;
    let enabled = false;
    const toggleButton = document.getElementById('alternar-sismos');
    const nativePopoverSelector = CSS.supports('selector(:popover-open)');
    const isOpen = hint => hint.classList.contains(':popover-open') || (nativePopoverSelector && hint.matches(':popover-open'));
    const [west, south, east, north] = data.metadata.filter.bounds_wsen;
    for (const feature of data.features) {
        const [lon, lat] = feature.geometry.coordinates;
        if (!(west <= lon && lon <= east && south <= lat && lat <= north)) {
            throw new Error(i18n.t("hay_un_epicentro_fuera_del_area_seleccionada"));
        }
        const container = document.createElement('div');
        container.className = 'sismo-marker';
        container.hidden = !enabled || map.getZoom() < minimumZoom;
        containers.push(container);
        const button = document.createElement('button');
        button.type = 'button'; button.className = 'sismo-icon';
        i18n.attr(button, 'aria-label', () => i18n.t("consultar_fecha_y_magnitud_del_sismo"));
        button.setAttribute('aria-expanded', 'false');
        button.dataset.eventId = feature.id;
        // Display bins for catalog magnitude, not observed seismic intensity.
        const value = feature.properties.magnitude;
        const color = !Number.isFinite(value) ? '#c6dce7'
            : value < 3 ? '#c8e64b' : value < 4 ? '#ffe04b'
            : value < 5 ? '#ff963b' : '#ff3b30';
        button.style.setProperty('--earthquake-color', color);
        i18n.html(button, '<svg viewBox="0 0 16 16" width="12" height="12" aria-hidden="true" focusable="false"><path d="M1 8h3l2-5 4 10 2-5h3"/></svg>');
        const hint = document.createElement('div');
        hint.id = `detalle-${feature.id}`; hint.className = 'sismo-tooltip';
        hint.setAttribute('popover', 'hint'); hint.setAttribute('role', 'tooltip');
        // Safari's unknown hint type behaves as manual; use auto for light dismiss.
        if (hint.popover !== 'hint') hint.setAttribute('popover', 'auto');
        const date = document.createElement('span');
        i18n.text(date, () => i18n.date(feature.properties.date, { day: '2-digit', month: '2-digit', year: 'numeric' }));
        const magnitude = document.createElement('strong');
        i18n.text(magnitude, () => i18n.t("magnitud_0", [Number.isFinite(feature.properties.magnitude) ? feature.properties.magnitude.toLocaleString(i18n.locale(), { minimumFractionDigits: 1, maximumFractionDigits: 1 }) : i18n.t("no_disponible49")]));
        hint.append(date, magnitude);
        button.setAttribute('interestfor', hint.id);
        button.setAttribute('popovertarget', hint.id);
        button.setAttribute('popovertargetaction', 'show');
        button.setAttribute('aria-controls', hint.id);
        container.append(button, hint);
        new maplibregl.Marker({element: container, anchor: 'center', pitchAlignment: 'viewport', rotationAlignment: 'viewport'})
            .setLngLat(feature.geometry.coordinates).addTo(map);
        // Explicit viewport positioning follows MapLibre's geographic marker,
        // including 3D terrain; it does not depend on CSS anchor support.
        function positionHint() {
            const rect = button.getBoundingClientRect();
            const width = hint.offsetWidth, height = hint.offsetHeight;
            hint.style.left = `${Math.max(8, Math.min(innerWidth - width - 8, rect.left + rect.width / 2 - width / 2))}px`;
            const top = rect.top - height - 4;
            hint.style.top = `${top >= 8 ? top : Math.min(innerHeight - height - 8, rect.bottom + 4)}px`;
        }
        hint.addEventListener('beforetoggle', event => {
            if (event.newState === 'open') {
                for (const other of hints) if (other !== hint && isOpen(other)) other.hidePopover();
                requestAnimationFrame(positionHint);
            }
        });
        hint.addEventListener('toggle', () => {
            button.setAttribute('aria-expanded', String(isOpen(hint)));
            if (isOpen(hint)) positionHint();
        });
        hints.push(hint);
    }
    // A hover detail should not remain detached when the map is moved.
    map.on('movestart', () => {
        for (const hint of hints) if (isOpen(hint)) hint.hidePopover();
    });
    function updateVisibility() {
        const hidden = !enabled || map.getZoom() < minimumZoom;
        if (toggleButton) toggleButton.setAttribute('aria-pressed', String(enabled));
        for (const container of containers) container.hidden = hidden;
        if (hidden) {
            for (const hint of hints) if (isOpen(hint)) hint.hidePopover();
        }
    }
    map.on('zoom', updateVisibility);
    if (toggleButton) {
        toggleButton.disabled = false;
        toggleButton.addEventListener('click', () => {
            enabled = !enabled;
            updateVisibility();
        });
    }
    updateVisibility();
}
