import requests
import json
import time
from typing import List, Dict, Set, Tuple

API_URL_TEMPLATE = "https://releases.moe/api/collections/entries/records?expand=trs&page={}"
ANILIST_API_URL = "https://graphql.anilist.co"

ANILIST_QUERY = """
query($ids: [Int]) {
  Page {
    media(id_in: $ids) {
      id
      title {
        english
        romaji
      }
      seasonYear
      format
      relations {
        edges {
          id
          relationType
          node {
            id
            title {
              romaji
            }
          }
        }
      }
    }
  }
}
"""

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

def query_anilist_batch(anilist_ids: List[int]) -> Dict[int, Dict]:
    """
    Query AniList API for a batch of anime IDs.
    Returns a dict mapping ID to anime data.
    """
    variables = {"ids": anilist_ids}
    
    response = requests.post(
        ANILIST_API_URL,
        json={"query": ANILIST_QUERY, "variables": variables}
    )
    response.raise_for_status()
    data = response.json()
    
    result = {}
    media_list = data.get("data", {}).get("Page", {}).get("media", [])
    
    for media in media_list:
        anime_id = media["id"]
        result[anime_id] = {
            "title_english": media["title"].get("english") or "",
            "title_romaji": media["title"].get("romaji") or "",
            "seasonYear": media.get("seasonYear"),
            "format": media.get("format"),
            "relations": media.get("relations", {}).get("edges", [])
        }
    
    return result

def fetch_anilist_data(entries: List[Dict]) -> Dict[int, Dict]:
    """
    Fetch AniList data for all entries in batches of 50 with 2s delay.
    """
    # Extract unique AniList IDs
    anilist_ids = set()
    for entry in entries:
        anilist_id = entry.get("alID")
        if anilist_id:
            anilist_ids.add(int(anilist_id))
    
    anilist_ids = sorted(anilist_ids)
    print(f"Fetching data for {len(anilist_ids)} unique AniList IDs...")
    
    all_data = {}
    batch_size = 50
    
    for i in range(0, len(anilist_ids), batch_size):
        batch = anilist_ids[i:i + batch_size]
        print(f"Querying AniList batch {i//batch_size + 1}/{(len(anilist_ids) + batch_size - 1)//batch_size}...")
        
        batch_data = query_anilist_batch(batch)
        all_data.update(batch_data)
        
        # Delay between batches (except for the last one)
        if i + batch_size < len(anilist_ids):
            time.sleep(2)
    
    print(f"Fetched AniList data for {len(all_data)} anime.")
    return all_data

def get_titles(entry: Dict, anilist_data: Dict[int, Dict]) -> Tuple[str, str]:
    """
    Get titles from AniList data.
    """
    anilist_id = int(entry.get("alID")) if entry.get("alID") else None
    
    if not anilist_id or anilist_id not in anilist_data:
        # Fallback to old behavior if AniList data not available
        titles = entry.get("titles", {})
        title_en = titles.get("english") or ""
        title_romaji = titles.get("romaji") or ""
    else:
        anime_data = anilist_data[anilist_id]
        title_en = anime_data["title_english"]
        title_romaji = anime_data["title_romaji"]
    
    if title_en:
        main_title = title_en
        alt_title = title_romaji
    else:
        main_title = title_romaji
        alt_title = ""

    if main_title == alt_title:
        alt_title = ""

    return main_title, alt_title

def build_relation_map(anilist_data: Dict[int, Dict]) -> Dict[int, List[int]]:
    """
    Build a mapping of parent anime to their related anime (sequels, side stories, etc).
    """
    relation_map = {}
    
    for anime_id, data in anilist_data.items():
        relations = data.get("relations", [])
        
        for edge in relations:
            relation_type = edge.get("relationType", "")
            related_id = edge.get("node", {}).get("id")
            
            # We care about relations that indicate hierarchy
            # SEQUEL, PREQUEL, SIDE_STORY, PARENT_STORY, etc.
            if related_id and relation_type in ["PARENT", "PREQUEL", "PARENT_STORY"]:
                # This anime is related to a parent
                if related_id not in relation_map:
                    relation_map[related_id] = []
                if anime_id not in relation_map[related_id]:
                    relation_map[related_id].append(anime_id)
    
    return relation_map

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

    # check for tracker-based not_nyaa
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

def parse_entries(entries: List[Dict], anilist_data: Dict[int, Dict]):
    anime_data = []
    seen_main_titles = set()

    for entry in entries:
        main_title, alt_title = get_titles(entry, anilist_data)
        parent_order = entry.get("parent", 0)
        anilist_id = int(entry.get("alID", 0)) if entry.get("alID") else 0

        if main_title in seen_main_titles and alt_title:
            main_title, alt_title = alt_title, main_title

        seen_main_titles.add(main_title)

        notes = entry.get("notes", "").strip()
        theoretical_best = entry.get("theoreticalBest", "").strip()
        comparison = entry.get("comparison", "").strip().replace(",", "\n")

        # Get year and format from AniList data
        year = None
        format_type = None
        if anilist_id and anilist_id in anilist_data:
            year = anilist_data[anilist_id].get("seasonYear")
            format_type = anilist_data[anilist_id].get("format")

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
                "year": year,
                "format": format_type,
                "notes": notes,
                "comparison": comparison,
                "release_rows": release_rows,
                "_parent_order": parent_order,
                "_anilist_id": anilist_id
            })

    return anime_data

def smart_sort_anime(anime_data: List[Dict], anilist_data: Dict[int, Dict]) -> List[Dict]:
    """
    Sort anime families alphabetically by first member, with year-based sorting within each family.
    
    Strategy:
    1. Build parent-child tree structure using PARENT/PREQUEL relations
    2. Group by root parent
    3. Within each group, sort ALL entries by year (ignoring hierarchy)
    4. When years match: prequels come before sequels, then alphabetical for siblings
    5. Sort groups alphabetically by the first entry's title in each family
    """
    
    # Build parent and children relationships
    parent_map = {}  # anime_id -> immediate parent_id
    children_map = {}  # parent_id -> [list of child_ids]
    
    for anime in anime_data:
        anime_id = anime.get("_anilist_id", 0)
        if not anime_id or anime_id not in anilist_data:
            continue
            
        relations = anilist_data[anime_id].get("relations", [])
        
        # PARENT relation takes priority over PREQUEL
        parent_id = None
        for relation in relations:
            if relation.get("relationType") == "PARENT":
                parent_id = relation.get("node", {}).get("id")
                if parent_id:
                    break
        
        if not parent_id:
            for relation in relations:
                if relation.get("relationType") == "PREQUEL":
                    parent_id = relation.get("node", {}).get("id")
                    if parent_id:
                        break
        
        if parent_id:
            parent_map[anime_id] = parent_id
            if parent_id not in children_map:
                children_map[parent_id] = []
            children_map[parent_id].append(anime_id)
    
    def find_root_parent(anime_id: int, visited: Set[int] = None) -> int:
        """Find ultimate root parent, avoiding cycles"""
        if visited is None:
            visited = set()
        if anime_id in visited or anime_id not in parent_map:
            return anime_id
        visited.add(anime_id)
        return find_root_parent(parent_map[anime_id], visited)
    
    # Build anime_id to anime object mapping
    id_to_anime = {}
    for anime in anime_data:
        anime_id = anime.get("_anilist_id", 0)
        if anime_id:
            id_to_anime[anime_id] = anime
    
    def get_year(anime_id: int) -> int:
        """Get year for an anime, returning 9999 if not available"""
        if anime_id in anilist_data:
            year = anilist_data[anime_id].get("seasonYear")
            if year:
                return year
        return 9999  # Unknown year goes to end
    
    def get_chronological_order(anime_id: int, anime_ids: Set[int]) -> int:
        """
        Get chronological position for tie-breaking.
        Count how many prequels this anime has among all entries in the family.
        Lower number = earlier in chronology = comes first.
        """
        if anime_id not in anilist_data:
            return 999
        
        relations = anilist_data[anime_id].get("relations", [])
        prequel_count = 0
        
        # Count how many prequels this anime has among the family
        for relation in relations:
            if relation.get("relationType") == "PREQUEL":
                prequel_id = relation.get("node", {}).get("id")
                if prequel_id and prequel_id in anime_ids:
                    prequel_count += 1
        
        return prequel_count
    
    # Group by root parent
    groups = {}  # root_id -> [anime_ids]
    standalone = []  # Anime without AniList ID
    
    for anime in anime_data:
        anime_id = anime.get("_anilist_id", 0)
        
        if not anime_id:
            standalone.append(anime)
            continue
        
        root_id = find_root_parent(anime_id)
        if root_id not in groups:
            groups[root_id] = []
        groups[root_id].append(anime_id)
    
    # Sort each group by year (flat sort, ignoring hierarchy)
    for root_id in groups:
        anime_ids_set = set(groups[root_id])
        groups[root_id].sort(key=lambda aid: (
            get_year(aid),
            get_chronological_order(aid, anime_ids_set),
            id_to_anime[aid]["main_title"].lower() if aid in id_to_anime else ""
        ))
    
    # Sort groups alphabetically by the first entry's title in each family
    group_sort_keys = []
    for root_id, anime_ids in groups.items():
        # Get the first entry's title (after year sorting within family)
        first_title = ""
        if anime_ids and anime_ids[0] in id_to_anime:
            first_title = id_to_anime[anime_ids[0]]["main_title"].lower()
        
        group_sort_keys.append((first_title, anime_ids))
    
    group_sort_keys.sort(key=lambda x: x[0])
    
    # Build final result
    result = []
    for _, anime_ids in group_sort_keys:
        for anime_id in anime_ids:
            if anime_id in id_to_anime:
                result.append(id_to_anime[anime_id])
    
    # Add standalone, sorted alphabetically
    standalone.sort(key=lambda x: x["main_title"].lower())
    result.extend(standalone)
    
    return result

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
            "year": anime.get("year"),
            "format": anime.get("format"),
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
    # Fetch releases.moe data
    entries = fetch_entries()
    
    # Fetch AniList data in batches
    anilist_data = fetch_anilist_data(entries)
    
    # Parse entries with AniList data
    anime_data = parse_entries(entries, anilist_data)
    
    # Smart sort to keep related anime together
    anime_data = smart_sort_anime(anime_data, anilist_data)
    
    # Write output
    write_json(anime_data)

if __name__ == "__main__":
    main()