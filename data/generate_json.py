import requests
import json

API_URL_TEMPLATE = "https://releases.moe/api/collections/entries/records?expand=trs&page={}"

def load_title_mapping():
    url = "https://raw.githubusercontent.com/anime-and-manga/lists/refs/heads/main/anime-full.json"
    response = requests.get(url)
    response.raise_for_status()
    title_mapping_raw = response.json()
    return {entry["idAL"]: entry["titles"] for entry in title_mapping_raw}

def fetch_entries():
    all_entries = []
    page = 1
    
    while True:
        url = API_URL_TEMPLATE.format(page)
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()
        
        items = data.get("items", [])
        if not items:
            break
        
        all_entries.extend(items)
        
        total_pages = data.get("totalPages", 1)
        if page >= total_pages:
            break
        
        page += 1
        print(f"Fetched page {page-1}/{total_pages}...")
    
    print(f"Total entries fetched: {len(all_entries)}")
    return all_entries

def get_titles(entry, title_mapping):
    al_id = entry.get("alID")
    titles = title_mapping.get(al_id, {})
    title_en = titles.get("english") or ""
    title_romaji = titles.get("romaji") or ""
    
    if title_en:
        main_title = title_en
        alt_title = title_romaji
    else:
        main_title = title_romaji
        alt_title = ""
    
    if main_title == alt_title:
        alt_title = ""
    
    return main_title, alt_title

def collect_release_metadata(torrents):
    release_metadata = {}
    release_group_trackers = {}
    best_releases = []
    alt_releases = []
    
    for tr in torrents:
        group = tr.get("releaseGroup", "")
        if not group:
            continue
        
        is_best = tr.get("isBest", False)
        is_dual = tr.get("dualAudio", False)
        tags = tr.get("tags", [])
        tracker = tr.get("tracker", "")
        
        formatted_group = f"{group} (Dual Audio)" if is_dual else group
        
        if formatted_group not in release_group_trackers:
            release_group_trackers[formatted_group] = set()
        release_group_trackers[formatted_group].add(tracker.lower())
        
        metadata_key = f"{formatted_group}|{is_best}"
        
        tags_lower = [tag.lower() for tag in tags]
        is_unmuxed = "unmuxed" in tags_lower
        is_broken = "broken" in tags_lower
        is_incomplete = "incomplete" in tags_lower
        
        if metadata_key not in release_metadata:
            release_metadata[metadata_key] = {
                "is_unmuxed": is_unmuxed,
                "is_broken": is_broken,
                "is_incomplete": is_incomplete,
                "is_not_nyaa": True
            }
        else:
            existing = release_metadata[metadata_key]
            existing["is_unmuxed"] = existing["is_unmuxed"] or is_unmuxed
            existing["is_broken"] = existing["is_broken"] or is_broken
            existing["is_incomplete"] = existing["is_incomplete"] or is_incomplete
        
        if is_best:
            if formatted_group not in best_releases:
                best_releases.append(formatted_group)
        else:
            if formatted_group not in alt_releases:
                alt_releases.append(formatted_group)
    
    for metadata_key in release_metadata:
        formatted_group = metadata_key.rsplit('|', 1)[0]
        trackers = release_group_trackers.get(formatted_group, set())
        release_metadata[metadata_key]["is_not_nyaa"] = "nyaa" not in trackers
    
    return release_metadata, best_releases, alt_releases

def deduplicate_releases(releases):
    groups = {}
    for release in releases:
        base_name = release.replace(" (Dual Audio)", "")
        if base_name not in groups:
            groups[base_name] = []
        groups[base_name].append(release)
    
    result = []
    for base_name, versions in groups.items():
        if len(versions) > 1:
            dual_version = f"{base_name} (Dual Audio)"
            if dual_version in versions:
                result.append(dual_version)
            else:
                result.append(versions[0])
        else:
            result.append(versions[0])
    return result

def parse_entries(entries, title_mapping):
    anime_data = []
    seen_main_titles = set()
    
    for entry in entries:
        main_title, alt_title = get_titles(entry, title_mapping)

        if main_title in seen_main_titles and alt_title:
            main_title, alt_title = alt_title, main_title

        seen_main_titles.add(main_title)

        notes = entry.get("notes", "").strip()
        theoretical_best = entry.get("theoreticalBest", "").strip()
        comparison = entry.get("comparison", "").strip().replace(",", "\n")
        
        torrents = entry.get("expand", {}).get("trs", [])
        release_metadata, best_releases, alt_releases = collect_release_metadata(torrents)
        
        if not best_releases and theoretical_best:
            best_releases.append(theoretical_best)
            metadata_key = f"{theoretical_best}|True"
            release_metadata[metadata_key] = {
                "is_unmuxed": "+" in theoretical_best,
                "is_broken": False,
                "is_incomplete": False,
                "is_not_nyaa": True
            }
        
        best_releases = deduplicate_releases(best_releases)
        alt_releases = deduplicate_releases(alt_releases)
        
        best_releases.sort()
        alt_releases.sort()
        
        if best_releases or alt_releases:
            max_releases = max(len(best_releases), len(alt_releases))
            best_releases_padded = best_releases + [""] * (max_releases - len(best_releases))
            alt_releases_padded = alt_releases + [""] * (max_releases - len(alt_releases))
            
            release_rows = []
            for best, alt in zip(best_releases_padded, alt_releases_padded):
                best_metadata_key = f"{best}|True" if best else None
                alt_metadata_key = f"{alt}|False" if alt else None
                
                release_rows.append({
                    "best": best,
                    "alt": alt,
                    "best_metadata": release_metadata.get(best_metadata_key, {}),
                    "alt_metadata": release_metadata.get(alt_metadata_key, {})
                })
            
            anime_data.append({
                "main_title": main_title,
                "alt_title": alt_title,
                "notes": notes,
                "comparison": comparison,
                "release_rows": release_rows
            })
    
    anime_data.sort(key=lambda x: x["main_title"].lower())
    return anime_data

def metadata_to_status(metadata):
    if not metadata:
        return ""
    if metadata.get("is_broken"):
        return "broken"
    if metadata.get("is_incomplete"):
        return "incomplete"
    if metadata.get("is_unmuxed"):
        return "unmuxed"
    if metadata.get("is_not_nyaa"):
        return "not_nyaa"
    return ""

def build_compact_rows(anime_data):
    rows = []
    for anime in anime_data:
        best_releases = []
        alt_releases = []

        for rr in anime["release_rows"]:
            best = (rr.get("best") or "").strip()
            alt = (rr.get("alt") or "").strip()

            if best:
                best_releases.append({
                    "name": best,
                    "status": metadata_to_status(rr.get("best_metadata", {})),
                })

            if alt:
                alt_releases.append({
                    "name": alt,
                    "status": metadata_to_status(rr.get("alt_metadata", {})),
                })

        rows.append({
            "title": anime["main_title"],
            "alt_title": anime["alt_title"],
            "notes": anime["notes"],
            "comparison": anime["comparison"],
            "best_releases": best_releases,
            "alt_releases": alt_releases,
        })

    return rows

def write_json(anime_data, out_path="releases.json"):
    rows = build_compact_rows(anime_data)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print(f"Wrote {out_path} ({len(rows)} anime entries).")

def main():
    title_mapping = load_title_mapping()
    entries = fetch_entries()
    anime_data = parse_entries(entries, title_mapping)
    write_json(anime_data)

if __name__ == "__main__":
    main()