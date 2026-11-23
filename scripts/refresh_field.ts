// Refreshes the archived M-C field with newer public Limitless open-team sheets.
// Run from inside pinned Champions Lab: cp ../scripts/refresh_field.ts scripts/pokeprotocol-refresh.ts && node scripts/pokeprotocol-refresh.ts
// Preserves September historical data, uses pinned Showdown validation, emits current 35-day field.
import fs from 'node:fs';
import path from 'node:path';
import {ROOT} from '../src/engine/vendor.ts';
import {loadDex} from '../src/engine/load.ts';
import {toID} from '../src/engine/dex.ts';
import {normalizeSet, validateTeam, statPointProblems} from '../src/engine/sets.ts';
import {ruleSpread} from '../src/engine/priors.ts';
import {hash32} from '../src/engine/stats.ts';

const MIN_PLAYERS = 24;
const MAX_EVENTS = 160;
const RECENT_DAYS = 35;
const API = 'https://play.limitlesstcg.com/api';
const CUTOFF = Date.parse('2026-09-09T02:00:00Z');
const MC_END = Date.parse('2026-12-02T02:00:00Z');
const now = Date.now();
const freshThreshold = now - 6 * 3600_000; // avoid ongoing tournaments
const recentSince = now - RECENT_DAYS * 86_400_000;
const inputPath = path.join(ROOT, 'data/field.json');
const reportPath = path.join(ROOT, 'data/pokeprotocol-refresh.json');
const recentPath = path.join(ROOT, 'data/field-recent.json');
const dex = loadDex();
const field = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
// Prune events explicitly identified as older regulations or singles.
const wrongReg = /\bm[ -]?[abd]\b|\breg(?:ulation)?\s*(?:a|b|d|f|h|i)\b|\bsingles?\b/i;
const mislabelledIds = new Set<string>((field.meta.sources || [])
  .filter((s: any) => s.reg === 'M-C' && wrongReg.test(String(s.name || '')))
  .map((s: any) => s.id));
field.meta.sources = (field.meta.sources || []).filter((s: any) => !mislabelledIds.has(s.id));
field.teams = field.teams.filter((t: any) => !mislabelledIds.has(t.eventId));
const pastSources = new Map<string, any>((field.meta.sources || []).map((s: any) => [s.id, s]));
const prior: Record<string, any> = field.spreadPrior || {};
const natureById = new Map<string, any>(dex.data.natures.map((n: any) => [n.id, n]));
const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));
const audit: any = {
  startedAt: new Date(now).toISOString(), source: API,
  format: 'gen9championsvgc2026regmc', recentDays: RECENT_DAYS, minPlayers: MIN_PLAYERS,
  baselineEvents: pastSources.size, baselineTeams: field.teams.length,
  attemptedEvents: 0, acceptedEvents: 0, acceptedTeams: 0, rejectedTeams: 0,
  skippedEvents: [], pagesScanned: 0, notes: [],
};

async function getJSON<T>(url: string): Promise<T> {
  for (let attempt = 0; attempt < 4; attempt++) {
    try {
      const res = await fetch(url, {headers: {'user-agent': 'pokeprotocol-lab/1.0 (open-source Pokemon team analysis)'},
        signal: AbortSignal.timeout(22000)});
      if (res.ok) return await res.json() as T;
      if ([429, 500, 502, 503, 504].includes(res.status) && attempt < 3) {
        const wait = Number(res.headers.get('retry-after'));
        await sleep(Math.min(30_000, (Number.isFinite(wait) && wait > 0 ? wait * 1000 : 1500 * 2 ** attempt)));
        continue;
      }
      throw new Error('Limitless HTTP ' + res.status + ' at ' + url);
    } catch (e) {
      if (attempt === 3) throw e;
      await sleep(800 * (attempt + 1));
    }
  }
  throw new Error('API did not return data');
}

function fixItem(raw: string): string {
  const id = toID(raw || '');
  if (!id || ['none','nothing','noitem'].includes(id)) return '';
  if (dex.getItem(id)) return dex.getItem(id)!.name;
  return raw || '';
}
function fixSpecies(species: string, item: string): string {
  const stone = dex.getItem(item);
  if (!stone?.megaStone) return species;
  const sp = dex.getSpecies(species);
  for (const base of Object.keys(stone.megaStone)) {
    const b = dex.getSpecies(base);
    if (b && sp && b.baseSpecies === sp.baseSpecies && b.id !== sp.id) return b.name;
  }
  return species;
}
function fixAbility(species: string, ability: string): string {
  const sp = dex.getSpecies(species);
  if (!sp) return ability;
  if (Object.values(sp.abilities).some(a => toID(String(a)) === toID(ability))) return ability;
  const megaAbility = (sp.megas || []).some(mid =>
    Object.values(dex.getSpecies(mid)?.abilities || {}).some(a => toID(String(a)) === toID(ability)));
  return megaAbility ? sp.abilities['0'] : ability;
}
function fillEvs(set: any) {
  const key = toID(set.species) + '|' + toID(set.nature);
  const base = dex.getSpecies(set.species)?.baseSpecies || set.species;
  const evs = prior[key] || prior[toID(base) + '|' + toID(set.nature)] ||
    ruleSpread(dex, set.species, set, natureById.get(toID(set.nature)));
  return {...set, evs: {...evs}};
}
function parseMon(m: any) {
  const sp = dex.getSpecies(m.id) || dex.getSpecies(m.name);
  const item = fixItem(String(m.item || ''));
  let species = fixSpecies(sp?.name || m.name || '', item);
  const moveStrings = (m.attacks || []).slice(0, 4).map((s: any) => String(s));
  if (species === 'Floette' && (moveStrings.includes('Light of Ruin') || toID(String(m.ability || '')) === 'fairyaura')) species = 'Floette-Eternal';
  const ability = fixAbility(species, String(m.ability || ''));
  const nature = natureById.get(toID(String(m.nature || '')))?.name || m.nature || 'Serious';
  return fillEvs(normalizeSet({species, item,
    ability: dex.getAbility(ability)?.name || ability, moves: moveStrings.map((s: string) => dex.getMove(s)?.name || s),
    nature, gender: ''}));
}
function countUsage(teams: any[]) {
  const mc = teams.filter(t => t.reg === 'M-C');
  const usage: Record<string, number> = {};
  for (const team of mc) for (const s of team.sets) {
    const id = toID(s.species); usage[id] = (usage[id] || 0) + 1;
  }
  for (const key of Object.keys(usage)) usage[key] = +(usage[key] / Math.max(1, mc.length)).toFixed(4);
  return usage;
}
function counts(teams: any[], sources: any[]) {
  return {teams: teams.length, mcTeams: teams.filter(t => t.reg === 'M-C').length,
    mbTeams: teams.filter(t => t.reg !== 'M-C').length, events: sources.length};
}

const listing: any[] = [];
for (let page = 1; page <= 12; page++) {
  const events = await getJSON<any[]>(API + '/tournaments?game=VGC&limit=100&page=' + page);
  audit.pagesScanned = page;
  if (!Array.isArray(events) || !events.length) break;
  listing.push(...events);
  if (events.some(e => Date.parse(e.date) < CUTOFF)) break;
  await sleep(160);
}
audit.listedEvents = listing.length;
const candidates = listing.filter(e => {
  const when = Date.parse(e.date);
  const name = String(e.name || '');
  return when >= CUTOFF && when < MC_END && when < freshThreshold && e.players >= MIN_PLAYERS &&
    !wrongReg.test(name);
}).sort((a,b) => Date.parse(b.date) - Date.parse(a.date)).slice(0, MAX_EVENTS);
audit.eligibleListed = candidates.length;
const newSources: any[] = [];
const newTeams: any[] = [];
let latest = '';

for (const event of candidates) {
  audit.attemptedEvents++;
  let standings: any[];
  try {
    standings = await getJSON<any[]>(API + '/tournaments/' + encodeURIComponent(event.id) + '/standings');
  } catch (e) {
    audit.skippedEvents.push({event: event.id, reason: String(e).slice(0,180)});
    continue;
  }
  if (!Array.isArray(standings)) {
    audit.skippedEvents.push({event: event.id, reason: 'no standings array'});
    continue;
  }
  const topcut = Math.max(8, Math.ceil(event.players / 8));
  let valid = 0;
  for (const s of standings) {
    if (!Array.isArray(s.decklist) || s.decklist.length !== 6) continue;
    try {
      const sets = s.decklist.map(parseMon);
      if (sets.some((x: any) => statPointProblems(x.evs).length)) { audit.rejectedTeams++; continue; }
      const verdict = validateTeam(sets);
      if (!verdict.ok) { audit.rejectedTeams++; continue; }
      const record = {wins: Number(s.record?.wins) || 0, losses: Number(s.record?.losses) || 0,
        ties: Number(s.record?.ties) || 0};
      const games = record.wins + record.losses + record.ties;
      if (games < 2) continue;
      const placing = Number(s.placing) || 999;
      newTeams.push({id: event.id + ':' + hash32(String(s.player)).toString(36), anon: true,
        reg: 'M-C', event: event.name, eventId: event.id, date: event.date.slice(0,10),
        players: event.players, placing, record,
        weight: +((record.wins + record.ties / 2 + 1) / (games + 2)).toFixed(4),
        top: placing <= topcut, sets});
      valid++;
    } catch (_) { audit.rejectedTeams++; }
  }
  if (!valid) {
    audit.skippedEvents.push({event: event.id, reason: 'no complete validated team sheets'});
    continue;
  }
  newSources.push({id: event.id, name: event.name, date: event.date.slice(0,10),
    players: event.players, reg: 'M-C', teams: valid, url: 'https://play.limitlesstcg.com/tournament/' + event.id + '/standings'});
  audit.acceptedEvents++;
  audit.acceptedTeams += valid;
  if (event.date > latest) latest = event.date;
  if (audit.attemptedEvents % 25 === 0) console.error('Checked', audit.attemptedEvents, 'events, accepted', audit.acceptedTeams, 'teams');
  await sleep(180);
}

if (newTeams.length < 5) throw new Error('Safety check: fewer than five validated recent teams fetched; refusing to overwrite baseline. ' + JSON.stringify(audit).slice(0,1200));

const refreshed = new Set(newSources.map(s => s.id));
const teams = [...field.teams.filter((t: any) => !refreshed.has(t.eventId)), ...newTeams];
const sources = [...pastSources.values()].filter((s: any) => !refreshed.has(s.id)).concat(newSources);
const asDate = (s: any) => Date.parse(s.date || '');
const generatedAt = new Date().toISOString();
const combined = {
  ...field, meta: {...field.meta, builtAt: generatedAt, sources,
    counts: {...field.meta.counts, ...counts(teams, sources)},
    pokeprotocol: {source: API, latestTournamentDate: latest.slice(0,10), acceptedEvents: newSources.length,
      recentDays: RECENT_DAYS, excludesIncomplete: true, noLiveMetagameGuarantee: true}},
  teams, usage: {...field.usage, mcTournaments: countUsage(teams)}
};
const recentTeams = teams.filter((t: any) => t.reg === 'M-C' && Date.parse(t.date) >= recentSince);
const recentSources = sources.filter((s: any) => s.reg === 'M-C' && Date.parse(s.date) >= recentSince);
if (recentTeams.length < 30 || recentSources.length < 3)
  throw new Error('Safety check: not enough recent teams for 35-day dataset: ' + recentTeams.length + ' / ' + recentSources.length);
const recent = {...combined, teams: recentTeams,
  meta: {...combined.meta, sources: recentSources,
    counts: counts(recentTeams, recentSources),
    pokeprotocol: {...combined.meta.pokeprotocol, recentOnly: true,
      windowStart: new Date(recentSince).toISOString().slice(0,10)}},
  usage: {...combined.usage, mcTournaments: countUsage(recentTeams)}};
audit.refreshedAt = generatedAt;
audit.latestTournamentDate = latest.slice(0,10);
audit.allCounts = counts(teams, sources);
audit.recentCounts = counts(recentTeams, recentSources);
audit.newestEvents = newSources.sort((a:any,b:any)=>b.date.localeCompare(a.date)).slice(0,12).map((s:any)=>({name:s.name,date:s.date,teams:s.teams,players:s.players,url:s.url}));
fs.writeFileSync(inputPath, JSON.stringify(combined));
fs.writeFileSync(recentPath, JSON.stringify(recent));
fs.writeFileSync(reportPath, JSON.stringify(audit, null, 2));
console.log(JSON.stringify({success:true, latest:audit.latestTournamentDate, acceptedEvents:audit.acceptedEvents,
  acceptedTeams:audit.acceptedTeams, all: audit.allCounts, recent: audit.recentCounts}, null, 2));
