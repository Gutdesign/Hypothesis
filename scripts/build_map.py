"""Build the static market map page from knowledge/companies/registry.csv.

  python scripts/build_map.py            writes site/index.html and site/registry.csv

The page is self-contained (data embedded as JSON), so it works from GitHub Pages or a local file.
The public CSV drops the internal `список_источника` column.
"""
import csv
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import registry  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

STAGES = [
    ("S0", "Стратегия, участки, ТЭО"), ("S1", "Сделка и кредит"), ("S2", "Изыскания"),
    ("S3", "Проектирование"), ("S4", "Разрешения"), ("S5", "Тендеры и закупки"),
    ("S6", "Строительство"), ("S7", "Сдача объекта"), ("S8a", "Эксплуатация"),
    ("S8b", "Аренда и продажа"), ("S9", "Реновация и ретрофит"),
    ("X-DATA", "Данные и среда данных"), ("X-FIN", "Финансы и страхование"),
    ("X-COMP", "Комплаенс и нормы"), ("X-EDU", "Образование"), ("none", "Этап не определён"),
]
STAGE_CODES = {c for c, _ in STAGES}
EU_OTHER = {"Германия", "Франция", "Португалия", "Швеция", "Австрия", "Швейцария", "Ирландия", "Люксембург",
            "Словения", "Италия", "Бельгия", "Дания", "Финляндия", "Норвегия"}
OUT = {"Индия", "Канада", "Япония", "Израиль", "ОАЭ"}


def region(country):
    if country == "США":
        return "США"
    if country in ("Великобритания", "Нидерланды", "Испания"):
        return country
    if country in EU_OTHER:
        return "Другая Европа"
    if country in OUT:
        return "Вне США и Европы"
    return "Не определён"


def kind(t):
    if t.startswith("продукт"):
        return "product"
    if t.startswith("крупный"):
        return "vendor"
    if t.startswith("строитель"):
        return "builder"
    return "services"


def norm_stage(s):
    s = s.strip()
    if not s or s == "н/д":
        return "none"
    m = re.match(r"^(S\d)([abcd]?)$", s)
    if m:
        base, sub = m.groups()
        if base == "S8":
            return "S8" + (sub or "a")
        return base
    return s if s in STAGE_CODES else "none"


def site_url(s):
    s = (s or "").strip()
    if not s or s == "н/д":
        return ""
    return s if s.startswith("http") else "https://" + s


def build_data(rows):
    out = []
    for r in rows:
        primary = norm_stage(r["этапы_основные"].replace(",", ";").split(";")[0])
        secondary = []
        for s in r["этапы_дополнительные"].replace(",", ";").split(";"):
            n = norm_stage(s)
            if n != "none" and n != primary and n not in secondary:
                secondary.append(n)
        kd = kind(r["тип_организации"])
        if kd in ("services", "builder") and primary == "none":
            primary = "none"
        out.append({
            "id": r["id"], "name": r["компания"], "site": site_url(r["сайт"]), "type": r["тип_организации"], "kind": kd,
            "primary": primary, "secondary": secondary, "role": r["роль_клиента"], "sub": r["подкатегория"],
            "markets": r["рынки_цель"], "city": r["штаб_город"], "country": r["штаб_страна"],
            "region": region(r["штаб_страна"]), "size": r["размер_сотрудников"], "round": r["последний_раунд"],
            "raised": r["привлечено"], "founded": r["год_основания"], "revenue": r["выручка"],
            "sources": [u for u in r["источники_данных"].split() if u.startswith("http")],
            "verified": r["данные_проверены"], "note": r["примечание"], "profile": r["профиль_по_списку"],
        })
    return out


TEMPLATE = r"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Карта строительных технологий</title>
<meta name="description" content="Реестр компаний, продуктов и крупных вендоров для строительной отрасли по этапам жизненного цикла объекта.">
<style>
:root{
  --bg:#f6f5f1; --panel:#ffffff; --ink:#1d2327; --muted:#5d6670; --line:#dcd9d0; --accent:#1f5f8b;
  --prod-bg:#e3eef6; --prod-ink:#143f5c; --vend-bg:#2b3640; --vend-ink:#f2f4f6; --build-bg:#f6e6c8; --build-ink:#5a3d05;
  --svc-bg:#e9e7e1; --svc-ink:#3d4349; --warn-bg:#fff4d6; --warn-ink:#5a4300; --focus:#c25b00;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --bg:#14181b; --panel:#1c2125; --ink:#e8ebed; --muted:#9aa4ad; --line:#2f373d; --accent:#6bb0dd;
  --prod-bg:#1d3a4e; --prod-ink:#cfe6f5; --vend-bg:#3a4651; --vend-ink:#f2f4f6; --build-bg:#4a3a14; --build-ink:#f6e3b8;
  --svc-bg:#2a3035; --svc-ink:#c9d0d6; --warn-bg:#3a3113; --warn-ink:#f1dfa5; --focus:#ffb066;}}
:root[data-theme="dark"]{
  --bg:#14181b; --panel:#1c2125; --ink:#e8ebed; --muted:#9aa4ad; --line:#2f373d; --accent:#6bb0dd;
  --prod-bg:#1d3a4e; --prod-ink:#cfe6f5; --vend-bg:#3a4651; --vend-ink:#f2f4f6; --build-bg:#4a3a14; --build-ink:#f6e3b8;
  --svc-bg:#2a3035; --svc-ink:#c9d0d6; --warn-bg:#3a3113; --warn-ink:#f1dfa5; --focus:#ffb066;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
a{color:var(--accent)}
.wrap{max-width:1500px;margin:0 auto;padding:20px 16px 48px}
h1{font-size:26px;line-height:1.2;margin:0 0 6px}
.sub{color:var(--muted);margin:0 0 14px;max-width:70ch}
.note{background:var(--warn-bg);color:var(--warn-ink);border-radius:8px;padding:10px 14px;margin:0 0 16px;max-width:90ch;font-size:14px}
.bar{display:flex;flex-wrap:wrap;gap:10px 18px;align-items:end;background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin-bottom:12px}
.bar label{display:flex;flex-direction:column;font-size:12px;color:var(--muted);gap:3px}
.bar select,.bar input[type=search]{font:inherit;color:var(--ink);background:var(--bg);border:1px solid var(--line);border-radius:6px;padding:6px 8px;min-width:150px}
.bar .chk{flex-direction:row;align-items:center;gap:6px;font-size:14px;color:var(--ink)}
.bar button{font:inherit;border:1px solid var(--line);background:var(--bg);color:var(--ink);border-radius:6px;padding:6px 10px;cursor:pointer}
.count{margin-left:auto;font-size:13px;color:var(--muted)}
.legend{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:13px;color:var(--muted);margin-bottom:12px}
.legend span{display:inline-flex;align-items:center;gap:6px}
.sw{width:14px;height:14px;border-radius:4px;display:inline-block}
.map{overflow-x:auto;border:1px solid var(--line);border-radius:10px;background:var(--panel)}
.grid{display:grid;grid-auto-flow:column;grid-auto-columns:minmax(190px,1fr);min-width:max-content}
.col{border-right:1px solid var(--line);min-width:190px}
.col:last-child{border-right:0}
.col.x{background:color-mix(in srgb,var(--panel) 92%,var(--accent) 8%)}
.hd{position:sticky;top:0;background:inherit;padding:10px 10px 8px;border-bottom:1px solid var(--line);z-index:1}
.hd b{display:block;font-size:12px;letter-spacing:.04em;color:var(--accent)}
.hd span{display:block;font-size:14px;font-weight:600;line-height:1.25}
.hd i{font-style:normal;font-size:12px;color:var(--muted)}
.cell{padding:8px;display:flex;flex-direction:column;gap:5px}
.chip{display:block;width:100%;text-align:left;border:0;border-radius:6px;padding:5px 8px;font:inherit;font-size:13px;line-height:1.3;cursor:pointer}
.chip small{display:block;opacity:.75;font-size:11px}
.chip.product{background:var(--prod-bg);color:var(--prod-ink)}
.chip.vendor{background:var(--vend-bg);color:var(--vend-ink)}
.chip.builder{background:var(--build-bg);color:var(--build-ink)}
.chip.services{background:var(--svc-bg);color:var(--svc-ink)}
.chip.sec{opacity:.5;border:1px dashed currentColor;background:transparent}
.chip:hover{filter:brightness(.96)}
:focus-visible{outline:3px solid var(--focus);outline-offset:2px}
.empty{color:var(--muted);font-size:12px;padding:4px 2px}
dialog{border:1px solid var(--line);border-radius:12px;background:var(--panel);color:var(--ink);padding:0;width:min(640px,calc(100vw - 24px));max-height:calc(100vh - 32px)}
dialog::backdrop{background:rgba(0,0,0,.45)}
.dh{display:flex;justify-content:space-between;gap:12px;align-items:start;padding:16px 18px 8px}
.dh h2{margin:0;font-size:20px;line-height:1.25}
.dh button{border:1px solid var(--line);background:var(--bg);color:var(--ink);border-radius:6px;padding:4px 10px;cursor:pointer;font:inherit}
.db{padding:0 18px 18px;overflow:auto;max-height:calc(100vh - 120px)}
.db dl{display:grid;grid-template-columns:150px 1fr;gap:6px 12px;margin:10px 0}
.db dt{color:var(--muted);font-size:13px}
.db dd{margin:0;overflow-wrap:anywhere}
.tag{display:inline-block;font-size:12px;border-radius:999px;padding:1px 9px;margin-right:6px}
.tag.product{background:var(--prod-bg);color:var(--prod-ink)}.tag.vendor{background:var(--vend-bg);color:var(--vend-ink)}
.tag.builder{background:var(--build-bg);color:var(--build-ink)}.tag.services{background:var(--svc-bg);color:var(--svc-ink)}
.src a{display:block;font-size:13px}
footer{margin-top:22px;color:var(--muted);font-size:13px;max-width:90ch}
@media (max-width:560px){.db dl{grid-template-columns:1fr}.count{margin-left:0;width:100%}}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
</style>
</head>
<body>
<div class="wrap">
  <h1>Карта строительных технологий</h1>
  <p class="sub">Компании по этапам жизненного цикла объекта: от выбора участка до эксплуатации и реновации. Нажмите на компанию, чтобы увидеть данные и источники.</p>
  <p class="note"><b>Как читать.</b> Данные собраны из агрегаторов, пресс-релизов и сайтов компаний; почти все строки проверены лишь частично. Суммы привлечённых денег и численность в разных источниках расходятся. Выручка стартапов в основном не раскрыта; где указана, это оценка агрегатора. Этапы присвоены по описанию продукта. Присутствие компании на карте показывает интерес и наличие продукта, а не спрос и не долю рынка. Список компаний неполон: в нём больше стартапов с внешними деньгами, чем местных игроков.</p>

  <div class="bar" role="search">
    <label>Поиск<input type="search" id="q" placeholder="название, роль, примечание"></label>
    <label>Тип<select id="fk"><option value="">Все</option><option value="product">Продукты</option><option value="vendor">Крупные вендоры</option><option value="builder">Строители и застройщики</option><option value="services">Услуги, консалтинг, образование</option></select></label>
    <label>Страна штаба<select id="fr"><option value="">Все</option></select></label>
    <label>Роль клиента<select id="fo"><option value="">Все</option></select></label>
    <label class="chk"><input type="checkbox" id="fs"> показывать и дополнительные этапы</label>
    <button type="button" id="reset">Сбросить</button>
    <button type="button" id="theme" aria-label="Переключить тему">Тема</button>
    <span class="count" id="count" aria-live="polite"></span>
  </div>
  <div class="legend" aria-hidden="true">
    <span><i class="sw" style="background:var(--prod-bg)"></i>продукт</span>
    <span><i class="sw" style="background:var(--vend-bg)"></i>крупный вендор</span>
    <span><i class="sw" style="background:var(--build-bg)"></i>строитель или застройщик</span>
    <span><i class="sw" style="background:var(--svc-bg)"></i>услуги, консалтинг, образование</span>
    <span><i class="sw" style="border:1px dashed var(--muted)"></i>дополнительный этап компании</span>
  </div>

  <div class="map"><div class="grid" id="grid"></div></div>

  <footer>
    <p>Снимок на __DATE__. Реестр: __COUNT__ строк. <a href="registry.csv">Скачать таблицу (CSV, разделитель «;», кодировка UTF-8 с BOM)</a>. Таксономия этапов — рабочий инструмент классификации, а не стандарт; «пустая» колонка не означает возможность: возможные причины — нет денег, регулирование, раздробленный покупатель или пробел в списке.</p>
  </footer>
</div>

<dialog id="dlg" aria-labelledby="dtitle">
  <div class="dh"><h2 id="dtitle"></h2><button type="button" id="close" aria-label="Закрыть">Закрыть</button></div>
  <div class="db" id="dbody"></div>
</dialog>

<script id="data" type="application/json">__DATA__</script>
<script>
(function(){
  var D = JSON.parse(document.getElementById('data').textContent);
  var STAGES = __STAGES__;
  var KIND = {product:'продукт',vendor:'крупный вендор',builder:'строитель или застройщик',services:'услуги, консалтинг, образование'};
  var $ = function(id){return document.getElementById(id)};
  var grid=$('grid'), q=$('q'), fk=$('fk'), fr=$('fr'), fo=$('fo'), fs=$('fs');
  function uniq(a){return a.filter(function(v,i){return v&&a.indexOf(v)===i})}
  uniq(D.map(function(c){return c.region})).sort().forEach(function(v){var o=document.createElement('option');o.value=o.textContent=v;fr.appendChild(o)});
  var roles=[]; D.forEach(function(c){c.role.split(';').forEach(function(r){r=r.trim(); if(r&&r!=='н/д')roles.push(r)})});
  uniq(roles).sort().forEach(function(v){var o=document.createElement('option');o.value=o.textContent=v;fo.appendChild(o)});

  function match(c){
    if(fk.value && c.kind!==fk.value) return false;
    if(fr.value && c.region!==fr.value) return false;
    if(fo.value && c.role.split(';').map(function(s){return s.trim()}).indexOf(fo.value)<0) return false;
    var t=q.value.trim().toLowerCase();
    if(t){var h=(c.name+' '+c.role+' '+c.sub+' '+c.note+' '+c.markets+' '+c.city+' '+c.country).toLowerCase(); if(h.indexOf(t)<0) return false}
    return true;
  }
  function order(a,b){var w={vendor:0,product:1,builder:2,services:3};return (w[a.kind]-w[b.kind])||a.name.localeCompare(b.name,'ru')}
  function chip(c,sec){
    var b=document.createElement('button'); b.type='button';
    b.className='chip '+c.kind+(sec?' sec':'');
    b.setAttribute('aria-label',c.name+', '+KIND[c.kind]+(sec?', дополнительный этап':''));
    b.textContent=c.name;
    if(c.country&&c.country!=='н/д'){var s=document.createElement('small');s.textContent=c.country;b.appendChild(s)}
    b.addEventListener('click',function(){open(c)});
    return b;
  }
  function render(){
    grid.textContent=''; var shown={};
    var list=D.filter(match); list.forEach(function(c){shown[c.id]=1});
    STAGES.forEach(function(st){
      var col=document.createElement('div'); col.className='col'+(st[0].indexOf('X-')===0?' x':'');
      var items=list.filter(function(c){return c.primary===st[0]}).sort(order);
      var sec=fs.checked?list.filter(function(c){return c.primary!==st[0]&&c.secondary.indexOf(st[0])>=0}).sort(order):[];
      var hd=document.createElement('div'); hd.className='hd';
      hd.innerHTML='<b></b><span></span><i></i>'; hd.children[0].textContent=st[0]==='none'?'—':st[0]; hd.children[1].textContent=st[1];
      hd.children[2].textContent=items.length+(sec.length?' + '+sec.length+' доп.':'')+' комп.';
      col.appendChild(hd);
      var cell=document.createElement('div'); cell.className='cell';
      if(!items.length&&!sec.length){var e=document.createElement('div');e.className='empty';e.textContent='нет компаний при этих фильтрах';cell.appendChild(e)}
      items.forEach(function(c){cell.appendChild(chip(c,false))});
      sec.forEach(function(c){cell.appendChild(chip(c,true))});
      col.appendChild(cell); grid.appendChild(col);
    });
    $('count').textContent='Показано '+list.length+' из '+D.length;
  }
  function row(dl,k,v){ if(!v||v==='н/д') v=null; var dt=document.createElement('dt');dt.textContent=k;var dd=document.createElement('dd');
    if(v===null){dd.textContent='н/д';dd.style.color='var(--muted)'} else dd.textContent=v; dl.appendChild(dt);dl.appendChild(dd); return dd}
  function open(c){
    $('dtitle').textContent=c.name;
    var b=$('dbody'); b.textContent='';
    var tg=document.createElement('p'); var t1=document.createElement('span'); t1.className='tag '+c.kind; t1.textContent=KIND[c.kind]; tg.appendChild(t1);
    if(c.sub){var t2=document.createElement('span');t2.textContent=c.sub;tg.appendChild(t2)} b.appendChild(tg);
    var dl=document.createElement('dl');
    var stg=STAGES.filter(function(s){return s[0]===c.primary||c.secondary.indexOf(s[0])>=0}).map(function(s){return (s[0]==='none'?'не определён':s[0]+' '+s[1])+(s[0]===c.primary?' (основной)':'')}).join('; ');
    row(dl,'Этапы',stg);
    row(dl,'Роль клиента',c.role);
    var loc=[c.city,c.country].filter(function(x){return x&&x!=='н/д'}).join(', '); row(dl,'Штаб',loc);
    row(dl,'Рынки',c.markets);
    row(dl,'Год основания',c.founded);
    row(dl,'Размер',c.size);
    row(dl,'Последний раунд',c.round);
    row(dl,'Привлечено',c.raised);
    row(dl,'Выручка',c.revenue);
    var sd=row(dl,'Сайт',c.site?' ':null); if(c.site){var a=document.createElement('a');a.href=c.site;a.target='_blank';a.rel='noopener noreferrer';a.textContent=c.site.replace(/^https?:\/\//,'');sd.textContent='';sd.appendChild(a)}
    row(dl,'Проверка данных',c.verified);
    if(c.note) row(dl,'Примечание',c.note);
    b.appendChild(dl);
    if(c.sources.length){var h=document.createElement('p');h.textContent='Источники';h.style.cssText='margin:12px 0 4px;color:var(--muted);font-size:13px';b.appendChild(h);
      var s=document.createElement('div');s.className='src';c.sources.forEach(function(u){var a=document.createElement('a');a.href=u;a.target='_blank';a.rel='noopener noreferrer';a.textContent=u.replace(/^https?:\/\//,'');s.appendChild(a)});b.appendChild(s)}
    $('dlg').showModal();
  }
  $('close').addEventListener('click',function(){$('dlg').close()});
  $('dlg').addEventListener('click',function(e){if(e.target===$('dlg'))$('dlg').close()});
  [q,fk,fr,fo,fs].forEach(function(el){el.addEventListener('input',render)});
  $('reset').addEventListener('click',function(){q.value='';fk.value='';fr.value='';fo.value='';fs.checked=false;render()});
  $('theme').addEventListener('click',function(){var r=document.documentElement;var cur=r.getAttribute('data-theme');
    var dark=cur?cur==='dark':window.matchMedia('(prefers-color-scheme: dark)').matches; r.setAttribute('data-theme',dark?'light':'dark');
    try{localStorage.setItem('theme',dark?'light':'dark')}catch(e){}});
  try{var th=localStorage.getItem('theme'); if(th)document.documentElement.setAttribute('data-theme',th)}catch(e){}
  render();
})();
</script>
</body>
</html>
"""


def main():
    rows = registry.read(registry.CSV_PATH)
    data = build_data(rows)
    SITE.mkdir(exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = (TEMPLATE.replace("__DATA__", payload)
            .replace("__STAGES__", json.dumps(STAGES, ensure_ascii=False))
            .replace("__DATE__", date.today().strftime("%d.%m.%Y"))
            .replace("__COUNT__", str(len(data))))
    (SITE / "index.html").write_text(html, encoding="utf-8")
    cols = [c for c in registry.COLUMNS if c != "список_источника"]
    with open(SITE / "registry.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter=";", extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})
    (SITE / ".nojekyll").write_text("", encoding="utf-8")
    print(f"wrote {SITE / 'index.html'} ({len(data)} companies, {len(html) // 1024} KB)")


if __name__ == "__main__":
    main()
