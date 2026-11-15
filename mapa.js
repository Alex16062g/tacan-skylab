import { abrirComparaciones } from "./resultados-python.js";
import { agregarSismos } from './recursos/sismos/sismos.js';

const loading = document.getElementById("map-loading");
const errorBox = document.getElementById("map-error");
const errorText = document.getElementById("map-error-text");
const view2D = document.getElementById("vista-2d");
const view3D = document.getElementById("vista-3d");
const layers = document.getElementById("map-layers");
const layerControl = document.getElementById("map-layer-control");
const layersToggle = document.getElementById("map-layers-toggle");
const mexicoBounds = [[-118.5, 14.3], [-86.5, 32.8]];
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

document.getElementById("map-retry").addEventListener("click", () => location.reload());

function showError(message) {
    loading.hidden = true;
    errorText.textContent = message;
    errorBox.hidden = false;
}

async function initializeMap() {
    const [maplibregl, volcanoData, metodologia] = await Promise.all([
        import("https://unpkg.com/maplibre-gl@6.18.0/dist/maplibre-gl.mjs"),
        fetch("./datos/tacana.json").then(response => {
            if (!response.ok) throw new Error("No se pudieron cargar los datos del Tacaná.");
            return response.json();
        }),
        fetch('./recursos/comparacion_tacana/metodologia.json').then(response => {
            if (!response.ok) throw new Error('No se pudo cargar el área analizada.');
            return response.json();
        })
    ]);
    const tacana = volcanoData.TACANA;
    const tacanaPosition = [tacana["Longitude (degrees east)"], tacana["Latitude (degrees north)"]];
    const [west, south, east, north] = metodologia.reference_source.sample_bounds_wsen;
    const areaTacana = { type: 'Feature', properties: {}, geometry: { type: 'Polygon',
        coordinates: [[[west, south], [east, south], [east, north], [west, north], [west, south]]] } };
    const terrainTiles = "https://tiles.mapterhorn.com/tilejson.json";
    const map = new maplibregl.Map({
        container: "mapa",
        center: [-102.5, 23.5],
        zoom: 4,
        pitch: 50,
        maxPitch: 60,
        minZoom: 2,
        // At zoom 13, 512 px map units match the provider's z14 / 256 px
        // tiles (~10 m/px). Further zoom only enlarges the same pixels.
        maxZoom: 13,
        renderWorldCopies: false,
        dragRotate: true,
        touchZoomRotate: true,
        touchPitch: true,
        keyboard: true,
        attributionControl: { customAttribution: '<a href="https://doi.org/10.21766/SSNMX/EC/MX" target="_blank" rel="noopener">Sismos: SSN / UNAM</a>' },
        locale: {
            "NavigationControl.ZoomIn": "Acercar",
            "NavigationControl.ZoomOut": "Alejar",
            "NavigationControl.ResetBearing": "Restablecer el norte",
            "FullscreenControl.Enter": "Pantalla completa",
            "FullscreenControl.Exit": "Salir de pantalla completa",
            "AttributionControl.ToggleAttribution": "Mostrar fuentes del mapa",
            "Map.Title": "Mapa de México"
        },
        style: {
            version: 8,
            sources: {
                cartografia: {
                    type: "raster",
                    tiles: ["https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless_3857/default/g/{z}/{y}/{x}.jpg"],
                    tileSize: 256,
                    maxzoom: 14,
                    attribution: '<a href="https://s2maps.eu">Sentinel-2 cloudless 2016</a> by <a href="https://eox.at">EOX IT Services GmbH</a> (Contains modified Copernicus Sentinel data 2016) · <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>'
                },
                elevacion: { type: "raster-dem", url: terrainTiles }
            },
            layers: [
                { id: "base-2d", type: "raster", source: "cartografia",
                    paint: { 'raster-brightness-min': 0.12, 'raster-brightness-max': 1, 'raster-saturation': 0.05 } }
            ],
            terrain: { source: "elevacion", exaggeration: 1 },
            sky: { "sky-color": "#d5e7f0", "horizon-color": "#edf4f7" }
        }
    });

    let is3D = true;
    const duration = () => reducedMotion.matches ? 0 : 700;

    function frameTacana() {
        map.fitBounds([[west, south], [east, north]], {
            padding: { top: 160, bottom: 60, left: 45, right: 65 },
            pitch: is3D ? 45 : 0,
            bearing: 0,
            duration: duration()
        });
    }

    const label = document.createElement("button");
    label.type = "button";
    label.disabled = true;
    label.className = "tacana-map-label";
    label.setAttribute("aria-label", "Volcán Tacaná, frontera México–Guatemala. Acercar y ver comparaciones con Luna y Marte");
    label.setAttribute("aria-controls", "comparison-MOON comparison-MARS");
    label.setAttribute("aria-expanded", "false");
    label.addEventListener("click", () => { frameTacana(); abrirComparaciones(label); });
    const name = document.createElement("strong");
    name.textContent = `Volcán ${tacana.Name}`;
    const location = document.createElement("span");
    location.textContent = "México / Guatemala";
    label.append(name, location);
    // Sin un anchor fijo, la etiqueta cambia de lado cuando se acerca a los bordes.
    new maplibregl.Popup({
        className: "tacana-popup",
        closeButton: false,
        closeOnClick: false,
        focusAfterOpen: false,
        offset: 80,
        maxWidth: "240px"
    })
        .setLngLat(tacanaPosition)
        .setDOMContent(label)
        .addTo(map);

    function changeView(enable3D) {
        is3D = enable3D;
        map.setTerrain(enable3D ? {
            source: "elevacion",
            exaggeration: 1
        } : null);
        view2D.checked = !enable3D;
        view3D.checked = enable3D;
        map.easeTo({ pitch: enable3D ? 60 : 0, duration: duration() });
    }

    function setLayersOpen(open) {
        layers.hidden = !open;
        layersToggle.setAttribute("aria-expanded", String(open));
    }

    function closeLayersOnOutsidePointer(event) {
        if (!layers.hidden && !layerControl.contains(event.target)) {
            setLayersOpen(false);
        }
    }

    layersToggle.addEventListener("click", () => setLayersOpen(layers.hidden));
    layerControl.addEventListener("keydown", event => {
        if (event.key === "Escape" && !layers.hidden) {
            event.preventDefault();
            event.stopPropagation();
            setLayersOpen(false);
            layersToggle.focus();
        }
    });

    map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "top-right");
    map.addControl(new maplibregl.FullscreenControl(), "top-right");
    map.addControl({
        onAdd() {
            document.addEventListener("pointerdown", closeLayersOnOutsidePointer);
            return layerControl;
        },
        onRemove() {
            document.removeEventListener("pointerdown", closeLayersOnOutsidePointer);
            layerControl.remove();
        }
    }, "top-right");
    const earthquakeControl = document.getElementById('earthquake-control');
    map.addControl({
        onAdd() { return earthquakeControl; },
        onRemove() { earthquakeControl.remove(); }
    }, 'top-right');
    map.addControl(new maplibregl.ScaleControl({ unit: "metric" }), "bottom-left");
    map.getCanvas().setAttribute("aria-label", "Mapa satelital interactivo de México");
    map.getCanvas().addEventListener("webglcontextlost", () => {
        showError("Se perdió la conexión con el procesador gráfico. Pulsa Reintentar para recuperar el mapa.");
    });

    map.on("error", event => {
        console.error('Error de cartografía:', event.error);
        showError("No se pudo cargar una capa del mapa. Comprueba tu conexión y pulsa Reintentar.");
    });

    map.fitBounds(mexicoBounds, { padding: 35, pitch: 50, bearing: 0, duration: 0 });

    map.on("load", () => {
        map.addSource('area-tacana', { type: 'geojson', data: areaTacana });
        map.addLayer({ id: 'area-tacana-fill', type: 'fill', source: 'area-tacana',
            paint: { 'fill-color': '#ffe16a', 'fill-opacity': 0.08 } });
        map.addLayer({ id: 'area-tacana-outline', type: 'line', source: 'area-tacana',
            paint: { 'line-color': '#ffe16a', 'line-width': 3 } });
        loading.hidden = true;
        layers.disabled = false;
        layersToggle.disabled = false;
        label.disabled = false;
        agregarSismos(map, maplibregl).catch(error => showError(error.message));
    });

    view2D.addEventListener("change", () => changeView(false));
    view3D.addEventListener("change", () => changeView(true));

    // El contenedor también puede cambiar de tamaño sin un resize de la ventana.
    const resizeObserver = new ResizeObserver(() => map.resize());
    resizeObserver.observe(document.getElementById("mapa"));
}

initializeMap().catch(() => {
    showError("No se pudo iniciar el mapa 3D. Comprueba tu conexión y que tu navegador tenga WebGL habilitado, y pulsa Reintentar.");
});
