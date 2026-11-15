import * as i18n from '../../idiomas/i18n.js';
const body=new URLSearchParams(location.search).get('body')==='MARS'?'MARS':'MOON';
const bodyName=body==='MOON'?i18n.t("luna"):i18n.t("marte");
const $=id=>document.getElementById(id);
const num=x=>Number.isFinite(x)?x.toLocaleString(i18n.locale(),{maximumFractionDigits:3}):i18n.t("sin_dato");
const range=(s,scale=1)=>s?`${num(s.min*scale)} – ${num(s.max*scale)}`:i18n.t("sin_observaciones");
document.querySelector(`[data-body="${body}"]`).setAttribute('aria-current','page');
$('retry').addEventListener('click',()=>location.reload());
function table(id,caption,headers,rows) {
  const wrapper=document.createElement('div');wrapper.className='table-wrapper';wrapper.tabIndex=0;
  wrapper.setAttribute('role','region');wrapper.setAttribute('aria-labelledby',`${id}-caption`);
  const t=document.createElement('table'),c=document.createElement('caption');c.id=`${id}-caption`;i18n.text(c, () => caption);
  const head=document.createElement('thead'),hrow=document.createElement('tr');
  for(const label of headers){const th=document.createElement('th');th.scope='col';i18n.text(th, () => label);hrow.append(th);}
  head.append(hrow);const tbody=document.createElement('tbody');
  for(const row of rows){const tr=document.createElement('tr');row.forEach((value,i)=>{const cell=document.createElement(i===0?'th':'td');if(i===0)cell.scope='row';i18n.text(cell, () => String(value));tr.append(cell);});tbody.append(tr);}
  t.append(c,head,tbody);wrapper.append(t);$(id).append(wrapper);
}
try {
  const response=await fetch('./ambiente_integrado.json',{cache:'no-store'});if(!response.ok)throw new Error(response.status);
  const data=await response.json(),region=data.bodies[body],power=data.reference_power;
  i18n.text($('title'), () => i18n.t("tacana_y_0_ambiente_y_radiacion", [bodyName]));
  i18n.title(() => i18n.t("ambiente_de_0_y_tacana", [bodyName]));
  const bounds=region.sector.match(/lat_(-?\d+)_(-?\d+)_lon_(\d+)_(\d+)/);
  i18n.text($('scope'), () => i18n.t("region_de_relieve_0_contexto_ambiental_del_sector_1_a_2_de_latitud_y_3_a", [region.name, bounds[1], bounds[2], bounds[3], bounds[4]]));
  table('thermal',i18n.t("rangos_observados_de_temperatura_superficial"),[i18n.t("fase"),'Tacaná (°C)',i18n.t("sector_de_0_c", [bodyName]),i18n.t("muestras_tacana_sector"),i18n.t("distancia_entre_distribuciones_c")],region.thermal.map(r=>[r.phase==='day'?i18n.t("dia"):i18n.t("noche"),range(r.tacana),range(r.planetary),`${r.tacana?.n??0} / ${r.planetary?.n??0}`,num(r.comparison?.distribution_distance_C)]));
  i18n.text($('power-scope'), () => i18n.t("0_1_dias_elevacion_de_la_celda_2_m_cima_3_m_datos_de_la_celda_no_de_la_c", [power.period, new Set(power.daily_records.map(r=>r.date)).size, num(power.cell_elevation_m), num(power.summit_elevation_m)]));
  table('power',i18n.t("nasa_power_rangos_de_valores_diarios"),[i18n.t("variable"),i18n.t("unidad"),i18n.t("minimo"),i18n.t("maximo"),i18n.t("dias_validos")],power.statistics.map(r=>[r.label,r.unit,num(r.statistics?.min),num(r.statistics?.max),r.statistics?.n??0]));
  $('power-source').href=power.source;
  if(region.pressure.length){
    table('pressure',i18n.t("presion_por_fecha"),[i18n.t("fecha"),i18n.t("celda_tacana_kpa"),i18n.t("sector_de_0_kpa", [bodyName]),i18n.t("perfiles_mcs")],region.pressure.map(r=>[r.date,num(power.daily_records.find(x=>x.date===r.date&&x.variable==='PS')?.value),range(r.statistics,.001),r.statistics.n]));
  } else i18n.text($('pressure'), () => body==='MOON'?i18n.t("exosfera_lunar_sin_serie_de_presion_regional_comparable_en_estos_archivo"):i18n.t("sin_observaciones_de_presion_en_este_sector"));
  if(region.atmospheric_temperature_106Pa.length){
    table('air',i18n.t("mcs_temperatura_por_fecha_en_el_sector"),[i18n.t("fecha"),i18n.t("minimo_c"),i18n.t("maximo_c"),i18n.t("perfiles")],region.atmospheric_temperature_106Pa.map(r=>[r.date,num(r.statistics.min),num(r.statistics.max),r.statistics.n]));
  } else i18n.text($('air'), () => body==='MOON'?i18n.t("no_corresponde_a_la_exosfera_lunar"):i18n.t("sin_observaciones_a_106_pa_en_este_sector"));
  table('solar',i18n.t("valores_de_referencia_del_cuerpo"),[i18n.t("magnitud"),i18n.t("tierra"),bodyName,i18n.t("unidad")],[[i18n.t("irradiancia_solar"),num(region.solar_reference.earth_W_m2),num(region.solar_reference.body_W_m2),'W/m²']]);
  $('solar-source').href=region.solar_reference.source;
  const atmosphere=data.atmosphere_context[body];$('composition-source').href=atmosphere.Source;
  if(body==='MARS') {
    table('composition',i18n.t("curiosity_sam_en_gale_no_mediciones_de_0", [region.name]),[i18n.t("componente"),i18n.t("fraccion_por_volumen")],[[i18n.t("oxigeno"),num(atmosphere['Oxygen By Volume (%)'])],[i18n.t("dioxido_de_carbono"),num(atmosphere['Carbon Dioxide By Volume (%)'])],[i18n.t("nitrogeno"),num(atmosphere['Nitrogen By Volume (%)'])],[i18n.t("argon"),num(atmosphere['Argon By Volume (%)'])]]);
  }else i18n.text($('composition'), () => i18n.t("exosfera_sin_mediciones_regionales_de_oxigeno_en_estos_datos"));
  i18n.text($('analysis'), () => i18n.t("0_comparaciones_termicas_por_sector_1_anova_termicos_exploratorios_2_gru", [data.existing_thermal_comparisons.length, data.existing_thermal_anova.length, data.mars_pressure_by_sector_date.length, data.mars_atmospheric_temperature_by_sector_date.length]));
  $('content').hidden=false;$('status').hidden=true;
} catch(error){console.error(error);i18n.text($('status'), () => i18n.t("no_se_pudieron_cargar_los_datos_ambientales"));$('retry').hidden=false;}
