import * as i18n from '../../idiomas/i18n.js';
const params=new URLSearchParams(location.search),body=params.get('body')==='MARS'?'MARS':'MOON',id=params.get('region');
const $=id=>document.getElementById(id);
const number=x=>Number.isFinite(x)?(x!==0&&Math.abs(x)<.001?x.toExponential(3):x.toLocaleString(i18n.locale(),{maximumFractionDigits:3})):'—';
const range=s=>s?(s.min===s.max?number(s.min):`${number(s.min)} – ${number(s.max)}`):i18n.t("sin_datos");
const states={missing_both:i18n.t("sin_insumos_de_ambos_lugares"),missing_planetary_data:i18n.t("sin_dato_planetario_comparable"),not_applicable_2m_air:i18n.t("no_aplicable_a_la_exosfera_lunar"),no_lunar_molecular_fraction:i18n.t("sin_fraccion_molecular_lunar_comparable"),body_reference:i18n.t("referencia_del_cuerpo"),descriptive_context:i18n.t("contexto_de_sector")};
function table(target,caption,headers,rows){
 if(!rows.length){i18n.text($(target), () => i18n.t("sin_observaciones_disponibles_para_este_sector"));return;}
 const wrap=document.createElement('div');wrap.className='table-wrapper';wrap.tabIndex=0;wrap.setAttribute('role','region');i18n.attr(wrap, 'aria-label', () => caption);
 const t=document.createElement('table'),c=document.createElement('caption');i18n.text(c, () => caption);
 const head=document.createElement('thead'),hr=document.createElement('tr');
 for(const label of headers){const th=document.createElement('th');th.scope='col';i18n.text(th, () => label);hr.append(th);}head.append(hr);
 const tb=document.createElement('tbody');for(const row of rows){const tr=document.createElement('tr');row.forEach((v,i)=>{const td=document.createElement(i?'td':'th');if(!i)td.scope='row';if(v instanceof Node)td.append(v);else i18n.text(td, () => String(v));tr.append(td);});tb.append(tr);}
 t.append(c,head,tb);wrap.append(t);$(target).append(wrap);
}
async function load(url){const r=await fetch(url,{cache:'no-store'});if(!r.ok)throw new Error(url);return r.json();}
try{
 const [catalog,profiles]=await Promise.all([load(`${body.toLowerCase()}.json`),load(`condiciones_${body.toLowerCase()}.json`)]);
 const f=catalog.features.find(x=>x.id===id);if(!f)throw new Error(i18n.t("region_no_encontrada"));
 const profile=profiles.profiles[f.conditions?.profile];if(!profile)throw new Error(i18n.t("sin_coordenadas_para_asignar_contexto"));
 i18n.text($('title'), () => `${f.name} · ${body==='MOON'?i18n.t("luna"):i18n.t("marte")}`);i18n.title(() => i18n.t("condiciones_de_0_tacana", [f.name]));
 $('back').href=`./index.html?body=${body}`;
 i18n.text($('scope'), () => i18n.t("0_latitud_1_e_sector_2_las_condiciones_ambientales_observadas_correspond", [number(f.latitude_deg), number(f.longitude_east_deg), profile.sector]));
 i18n.text($('coverage'), () => i18n.t("0_condiciones_registradas_1_4_tipos_de_observacion_sectorial_disponibles", [profiles.condition_count, profile.observation_types_available]));
 table('conditions',i18n.t("condiciones_cobertura_y_comparacion_por_variable"),[i18n.t("condicion"),i18n.t("unidad"),i18n.t("tacana_tierra"),i18n.t("region_cuerpo"),'Δ',i18n.t("cobertura_y_procedencia")],profile.conditions.map(c=>{
   const detail=document.createElement('div');detail.append(i18n.node(() => `${i18n.localize(states[c.status]??c.status)}. ${i18n.localize(c.scope)}. ${i18n.localize(c.period)} `));
   if(c.source){const a=document.createElement('a');i18n.text(a, () => i18n.t("fuente"));a.href=c.source;a.target='_blank';a.rel='noopener';detail.append(a);}
   return [c.label,c.unit,range(c.reference),range(c.planetary),number(c.difference),detail];
 }));
 table('thermal',i18n.t("observaciones_separadas_por_fase_y_periodo"),[i18n.t("tipo"),i18n.t("fase_hora_solar_local"),i18n.t("periodo"),i18n.t("minimo_c"),i18n.t("maximo_c"),i18n.t("celdas")],profile.additional_thermal_observations.map(r=>[r.temperature_type,r.phase,r.period,number(r.statistics.min),number(r.statistics.max),r.statistics.n]));
 table('pressure',i18n.t("presion_superficial_mcs_del_sector"),[i18n.t("fecha"),i18n.t("minimo_pa"),i18n.t("maximo_pa"),i18n.t("perfiles")],profile.pressure_other_dates.map(r=>[r.date,number(r.statistics.min),number(r.statistics.max),r.statistics.n]));
 table('atmosphere',i18n.t("temperatura_mcs_a_106_pa_no_aire_a_2_m"),[i18n.t("fecha"),i18n.t("minimo_c"),i18n.t("maximo_c"),i18n.t("perfiles")],profile.atmospheric_106Pa.map(r=>[r.date,number(r.statistics.min),number(r.statistics.max),r.statistics.n]));
 i18n.text($('terrain'), () => i18n.t("indice_de_relieve_0_100_elevacion_del_punto_1_m_referencia_vertical_plan", [number(f.global_similarity?.percent), number(f.global_terrain_context?.center_elevation_m), number(f.global_terrain_context?.slope_10km_deg)]));
 $('official').href=f.source_url;$('download').href=`./condiciones_${body.toLowerCase()}.json`;
 $('status').hidden=true;$('content').hidden=false;
}catch(e){console.error(e);i18n.text($('status'), () => i18n.t("no_se_pudieron_cargar_las_condiciones_de_este_lugar_vuelve_al_catalogo_y"));}
