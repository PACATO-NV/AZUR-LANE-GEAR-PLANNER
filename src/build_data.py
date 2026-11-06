import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import json, re
d = json.load(open(ROOT+'/data/regal_raw.json')); GM = d['GM']; REQ = d['EQ']
L = {x['id']: x for x in json.load(open(ROOT+'/data/equip_lite.json'))}
SG = json.load(open(ROOT+'/data/ship_group.json'))
NAT = {'USS':'유니온','HMS':'로열','IJN':'사쿠라','KMS':'철혈','ROC':'동煌','RN':'사르데냐','SN':'북방연합','FFNF':'아이리스','MNF':'비시아','DEV':'META'}
# equipment table: id -> [kr name, rarity, type, nation code]
E = {}
for i, x in L.items():
    E[i] = [x['name'], x['rarity'], x['type'], x.get('nation_code') or '']
used = set()
def ids_of(k):
    v = GM['equip'][str(k)]
    return v if isinstance(v, list) else [v]
for k in GM['equip']:
    for x in ids_of(k): used.add(x['id'])
for i in used:
    if i not in E and str(i) in REQ:
        r = REQ[str(i)]; E[i] = [r['name'], r['rarity'], 0, '']
# usecases with 5 slots only
U = {k: v for k, v in GM['usecase'].items() if len(v) == 5}
need_slot = {s for v in U.values() for s in v}
SL = {str(s): GM['slot'][str(s)] for s in need_slot if str(s) in GM['slot']}
need_row = {r for v in SL.values() for r in v}
# loadouts
ships_out = []
en2kr = {}
for s in d['ships']:
    base = re.sub(r'\s*\(.*$', '', s['n'])
    en2kr[base] = SG.get(str(s['g']), {}).get('name', base)
WORDS = {'Retrofit':'개','combo':'콤보','Fighter':'전투기형','Dive Bomber':'폭격기형','Main':'메인','damage':'딜러형','healer':'힐러형','CV':'항모형','BB':'전함형','Out of Ammo':'탄약 소진'}
def variant(n):
    base = re.sub(r'\s*\(.*$', '', n); kr = en2kr.get(base, base)
    parts = re.findall(r'\(([^)]*)\)', n); out = kr; extra = []
    for p in parts:
        if p == 'Retrofit': out += ' 개'; continue
        if p in WORDS: extra.append(WORDS[p]); continue
        m = re.match(r'with (.*)', p)
        if m:
            names = re.split(r'\s*(?:,| or |/)\s*', m.group(1))
            MAN={'Soyuz':'소유즈','AmagiCV':'아마기(항모)','UR IJN CVs':'UR 사쿠라 항모','USS CV':'유니온 항모','BBs':'전함','CVs':'항모','Ning':'닝하이','Ping':'핑하이','Nakhimov':'나히모프'}
            names = [WORDS.get(x) or MAN.get(x) or en2kr.get(x, x) for x in names if x]
            extra.append(('·'.join(names)) + ' 동반'); continue
        extra.append(p)
    return out + (' (' + ', '.join(extra) + ')' if extra else '')
for s in d['ships']:
    gear = GM['ship'].get(str(s['gear'])) if s.get('gear') else None
    lo = GM['ship'].get(str(s['lo'])) if s['lo'] else None
    st = None
    sm = GM['slotsMeta'].get(str(s['sl']))
    if sm: st = [GM['slotMeta'][str(m)][0] for m in sm]
    rt = s['rt'] or {}
    tabs = {t: u for t, u in (gear or {}).items() if str(u) in U}
    if lo:
        for rows in lo.values(): need_row.update(rows)
    ships_out.append([s['u'], variant(s['n']), s['n'], s['h'], s['f'], s['r'], [rt.get('a'), rt.get('b'), rt.get('c'), rt.get('d'), rt.get('m')], st, tabs, lo, s['hl']])
RW = {str(r): GM['row'][str(r)] for r in need_row if str(r) in GM['row']}
need_ek = {k for v in RW.values() for k in v}
EK = {}
for k in need_ek:
    v = GM['equip'][str(k)]
    EK[str(k)] = [x['id'] for x in v] if isinstance(v, list) else v['id']
# per-entry notes like 'lower rarity ok'
notes = {}
for k in need_ek:
    v = GM['equip'][str(k)]
    for j, x in enumerate(v if isinstance(v, list) else [v]):
        if x.get('name'): notes.setdefault(x['id'], x['name'])
DATA = dict(E=E, S=ships_out, U=U, SL=SL, RW=RW, EK=EK, NOTE=notes, NAT=NAT, date='2026-11-07')
s = json.dumps(DATA, ensure_ascii=False, separators=(',', ':'))
open(ROOT+'/data/app_data.json', 'w').write(s)
print(len(s), len(ships_out), len(E))
for n in ['Essex (Retrofit) (combo)','Aquila (with Musashi, Fighter)','Shinano (with Hakuhou/AmagiCV)','Admiral Nakhimov (with Moskva or Soyuz)']:
    print(n, '->', variant(n))
print({k:v for k,v in notes.items()} )

# build the page: src/app_template.html + data -> al_gear_planner.html (artifact body) and index.html (standalone)
tpl = open(ROOT + '/src/app_template.html').read()
page = tpl.replace('__DATA__', s.replace('</', '<\\/'))
open(ROOT + '/al_gear_planner.html', 'w').write(page)
seed_inv = open(ROOT + '/seed/inventory.json').read(); seed_fl = open(ROOT + '/seed/fleets.json').read()
pre = ('<script>try{if(!localStorage.getItem("al-inv")){localStorage.setItem("al-inv",JSON.stringify(' + seed_inv + '.counts));'
       'localStorage.setItem("al-fleets",JSON.stringify(' + seed_fl + '.fleets));}}catch(e){}</script>')
open(ROOT + '/index.html', 'w').write('<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"></head><body style="margin:0">' + pre + page + '</body></html>')
