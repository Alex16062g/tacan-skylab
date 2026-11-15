const body=new URLSearchParams(location.search).get('body')==='MARS'?'MARS':'MOON';
const bodyName=body==='MOON'?'Luna':'Marte';
const $=id=>document.getElementById(id);
const num=x=>Number.isFinite(x)?x.toLocaleString('es-MX',{maximumFractionDigits:3}):'Sin dato';
const range=(s,scale=1)=>s?`${num(s.min*scale)} – ${num(s.max*scale)}`:'Sin observaciones';
document.querySelector(`[data-body="${body}"]`).setAttribute('aria-current','page');
$('retry').addEventListener('click',()=>location.reload());
function table(id,caption,headers,rows) {
  const wrapper=document.createElement('div');wrapper.className='table-wrapper';wrapper.tabIndex=0;
  wrapper.setAttribute('role','region');wrapper.setAttribute('aria-labelledby',`${id}-caption`);
  const t=document.createElement('table'),c=document.createElement('caption');c.id=`${id}-caption`;c.textContent=caption;
  const head=document.createElement('thead'),hrow=document.createElement('tr');
  for(const label of headers){const th=document.createElement('th');th.scope='col';th.textContent=label;hrow.append(th);}
  head.append(hrow);const tbody=document.createElement('tbody');
  for(const row of rows){const tr=document.createElement('tr');row.forEach((value,i)=>{const cell=document.createElement(i===0?'th':'td');if(i===0)cell.scope='row';cell.textContent=String(value);tr.append(cell);});tbody.append(tr);}
  t.append(c,head,tbody);wrapper.append(t);$(id).append(wrapper);
}
try {
  const response=await fetch('./ambiente_integrado.json',{cache:'no-store'});if(!response.ok)throw new Error(response.status);
  const data=await response.json(),region=data.bodies[body],power=data.reference_power;
  $('title').textContent=`Tacaná y ${bodyName}: ambiente y radiación`;
  document.title=`Ambiente de ${bodyName} y Tacaná`;
  const bounds=region.sector.match(/lat_(-?\d+)_(-?\d+)_lon_(\d+)_(\d+)/);
  $('scope').textContent=`Región de relieve: ${region.name}. Contexto ambiental del sector ${bounds[1]}° a ${bounds[2]}° de latitud y ${bounds[3]}° a ${bounds[4]}° E de longitud; no mediciones locales del accidente.`;
  table('thermal','Rangos observados de temperatura superficial',['Fase','Tacaná (°C)',`Sector de ${bodyName} (°C)`,'Muestras Tacaná / sector','Distancia entre distribuciones (°C)'],region.thermal.map(r=>[r.phase==='day'?'Día':'Noche',range(r.tacana),range(r.planetary),`${r.tacana?.n??0} / ${r.planetary?.n??0}`,num(r.comparison?.distribution_distance_C)]));
  $('power-scope').textContent=`${power.period} · ${new Set(power.daily_records.map(r=>r.date)).size} días. Elevación de la celda: ${num(power.cell_elevation_m)} m; cima: ${num(power.summit_elevation_m)} m. Datos de la celda, no de la cima. Este periodo no representa una climatología.`;
  table('power','NASA POWER: rangos de valores diarios',['Variable','Unidad','Mínimo','Máximo','Días válidos'],power.statistics.map(r=>[r.label,r.unit,num(r.statistics?.min),num(r.statistics?.max),r.statistics?.n??0]));
  $('power-source').href=power.source;
  if(region.pressure.length){
    table('pressure','Presión por fecha',['Fecha','Celda Tacaná (kPa)',`Sector de ${bodyName} (kPa)`,'Perfiles MCS'],region.pressure.map(r=>[r.date,num(power.daily_records.find(x=>x.date===r.date&&x.variable==='PS')?.value),range(r.statistics,.001),r.statistics.n]));
  } else $('pressure').textContent=body==='MOON'?'Exosfera lunar: sin serie de presión regional comparable en estos archivos.':'Sin observaciones de presión en este sector.';
  if(region.atmospheric_temperature_106Pa.length){
    table('air','MCS: temperatura por fecha en el sector',['Fecha','Mínimo (°C)','Máximo (°C)','Perfiles'],region.atmospheric_temperature_106Pa.map(r=>[r.date,num(r.statistics.min),num(r.statistics.max),r.statistics.n]));
  } else $('air').textContent=body==='MOON'?'No corresponde a la exosfera lunar.':'Sin observaciones a 106 Pa en este sector.';
  table('solar','Valores de referencia del cuerpo',['Magnitud','Tierra',bodyName,'Unidad'],[['Irradiancia solar',num(region.solar_reference.earth_W_m2),num(region.solar_reference.body_W_m2),'W/m²']]);
  $('solar-source').href=region.solar_reference.source;
  const atmosphere=data.atmosphere_context[body];$('composition-source').href=atmosphere.Source;
  if(body==='MARS') {
    table('composition',`Curiosity / SAM en Gale; no mediciones de ${region.name}`,['Componente','Fracción por volumen (%)'],[['Oxígeno',num(atmosphere['Oxygen By Volume (%)'])],['Dióxido de carbono',num(atmosphere['Carbon Dioxide By Volume (%)'])],['Nitrógeno',num(atmosphere['Nitrogen By Volume (%)'])],['Argón',num(atmosphere['Argon By Volume (%)'])]]);
  }else $('composition').textContent='Exosfera. Sin mediciones regionales de oxígeno en estos datos.';
  $('analysis').textContent=`${data.existing_thermal_comparisons.length} comparaciones térmicas por sector; ${data.existing_thermal_anova.length} ANOVA térmicos exploratorios; ${data.mars_pressure_by_sector_date.length} grupos de presión por sector y fecha; ${data.mars_atmospheric_temperature_by_sector_date.length} grupos de temperatura atmosférica.`;
  $('content').hidden=false;$('status').hidden=true;
} catch(error){console.error(error);$('status').textContent='No se pudieron cargar los datos ambientales.';$('retry').hidden=false;}
