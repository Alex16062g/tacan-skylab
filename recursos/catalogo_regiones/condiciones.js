const params=new URLSearchParams(location.search),body=params.get('body')==='MARS'?'MARS':'MOON',id=params.get('region');
const $=id=>document.getElementById(id);
const number=x=>Number.isFinite(x)?(x!==0&&Math.abs(x)<.001?x.toExponential(3):x.toLocaleString('es-MX',{maximumFractionDigits:3})):'—';
const range=s=>s?(s.min===s.max?number(s.min):`${number(s.min)} – ${number(s.max)}`):'Sin datos';
const states={missing_both:'Sin insumos de ambos lugares',missing_planetary_data:'Sin dato planetario comparable',not_applicable_2m_air:'No aplicable a la exosfera lunar',no_lunar_molecular_fraction:'Sin fracción molecular lunar comparable',body_reference:'Referencia del cuerpo',descriptive_context:'Contexto de sector'};
function table(target,caption,headers,rows){
 if(!rows.length){$(target).textContent='Sin observaciones disponibles para este sector.';return;}
 const wrap=document.createElement('div');wrap.className='table-wrapper';wrap.tabIndex=0;wrap.setAttribute('role','region');wrap.setAttribute('aria-label',caption);
 const t=document.createElement('table'),c=document.createElement('caption');c.textContent=caption;
 const head=document.createElement('thead'),hr=document.createElement('tr');
 for(const label of headers){const th=document.createElement('th');th.scope='col';th.textContent=label;hr.append(th);}head.append(hr);
 const tb=document.createElement('tbody');for(const row of rows){const tr=document.createElement('tr');row.forEach((v,i)=>{const td=document.createElement(i?'td':'th');if(!i)td.scope='row';if(v instanceof Node)td.append(v);else td.textContent=String(v);tr.append(td);});tb.append(tr);}
 t.append(c,head,tb);wrap.append(t);$(target).append(wrap);
}
async function load(url){const r=await fetch(url,{cache:'no-store'});if(!r.ok)throw new Error(url);return r.json();}
try{
 const [catalog,profiles]=await Promise.all([load(`${body.toLowerCase()}.json`),load(`condiciones_${body.toLowerCase()}.json`)]);
 const f=catalog.features.find(x=>x.id===id);if(!f)throw new Error('Región no encontrada');
 const profile=profiles.profiles[f.conditions?.profile];if(!profile)throw new Error('Sin coordenadas para asignar contexto');
 $('title').textContent=`${f.name} · ${body==='MOON'?'Luna':'Marte'}`;document.title=`Condiciones de ${f.name} | Tacaná`;
 $('back').href=`./index.html?body=${body}`;
 $('scope').textContent=`${number(f.latitude_deg)}° latitud, ${number(f.longitude_east_deg)}° E. Sector: ${profile.sector}. Las condiciones ambientales observadas corresponden a sectores de 30° × 60°; las constantes generales corresponden al cuerpo.`;
 $('coverage').textContent=`${profiles.condition_count} condiciones registradas · ${profile.observation_types_available}/4 tipos de observación sectorial disponibles (temperatura superficial diurna/nocturna, presión y temperatura a 106 Pa). Sin mediciones ambientales locales asignadas a este accidente.`;
 table('conditions','Condiciones, cobertura y comparación por variable',['Condición','Unidad','Tacaná / Tierra','Región / cuerpo','Δ','Cobertura y procedencia'],profile.conditions.map(c=>{
   const detail=document.createElement('div');detail.append(document.createTextNode(`${states[c.status]??c.status}. ${c.scope}. ${c.period} `));
   if(c.source){const a=document.createElement('a');a.textContent='Fuente';a.href=c.source;a.target='_blank';a.rel='noopener';detail.append(a);}
   return [c.label,c.unit,range(c.reference),range(c.planetary),number(c.difference),detail];
 }));
 table('thermal','Observaciones separadas por fase y periodo',['Tipo','Fase (hora solar local)','Periodo','Mínimo (°C)','Máximo (°C)','Celdas'],profile.additional_thermal_observations.map(r=>[r.temperature_type,r.phase,r.period,number(r.statistics.min),number(r.statistics.max),r.statistics.n]));
 table('pressure','Presión superficial MCS del sector',['Fecha','Mínimo (Pa)','Máximo (Pa)','Perfiles'],profile.pressure_other_dates.map(r=>[r.date,number(r.statistics.min),number(r.statistics.max),r.statistics.n]));
 table('atmosphere','Temperatura MCS a 106 Pa: no aire a 2 m',['Fecha','Mínimo (°C)','Máximo (°C)','Perfiles'],profile.atmospheric_106Pa.map(r=>[r.date,number(r.statistics.min),number(r.statistics.max),r.statistics.n]));
 $('terrain').textContent=`Índice de relieve: ${number(f.global_similarity?.percent)} / 100. Elevación del punto: ${number(f.global_terrain_context?.center_elevation_m)} m (referencia vertical planetaria). Pendiente a 10 km: ${number(f.global_terrain_context?.slope_10km_deg)}°.`;
 $('official').href=f.source_url;$('download').href=`./condiciones_${body.toLowerCase()}.json`;
 $('status').hidden=true;$('content').hidden=false;
}catch(e){console.error(e);$('status').textContent='No se pudieron cargar las condiciones de este lugar. Vuelve al catálogo y abre su ficha.';}
