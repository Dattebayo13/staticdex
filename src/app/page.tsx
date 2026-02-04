import releases from "../../data/releases.json";

type ReleaseEntry = {
  title: string;
  alt_title: string;
  notes: string;
  comparison: string;
  best_releases: { name: string; status: string }[];
  alt_releases: { name: string; status: string }[];
};

type ReleaseRow = {
  title: string;
  alt_title: string;
  notes: string;
  comparison: string;
  best_name: string;
  best_status: string;
  alt_name: string;
  alt_status: string;
  isFirstForTitle: boolean;
  rowSpan: number;
};

function flattenToRows(data: ReleaseEntry[]): ReleaseRow[] {
  const rows: ReleaseRow[] = [];

  data.forEach((entry) => {
    const maxLen = Math.max(entry.best_releases.length || 1, entry.alt_releases.length || 1);

    for (let i = 0; i < maxLen; i++) {
      const best = entry.best_releases[i] ?? { name: "", status: "" };
      const alt = entry.alt_releases[i] ?? { name: "", status: "" };

      rows.push({
        title: entry.title,
        alt_title: entry.alt_title,
        notes: entry.notes,
        comparison: entry.comparison,
        best_name: best.name,
        best_status: best.status,
        alt_name: alt.name,
        alt_status: alt.status,
        isFirstForTitle: i === 0,
        rowSpan: 0,
      });
    }
  });

  let currentTitle: string | null = null;
  let groupStart = 0;

  for (let i = 0; i <= rows.length; i++) {
    const row = rows[i];
    if (i === 0) {
      currentTitle = row?.title ?? null;
      groupStart = 0;
      continue;
    }

    const titleChanged = !row || row.title !== currentTitle;
    if (titleChanged && currentTitle !== null) {
      const groupEnd = i;
      const span = groupEnd - groupStart;
      if (span > 0) {
        rows[groupStart].rowSpan = span;
        for (let j = groupStart + 1; j < groupEnd; j++) {
          rows[j].rowSpan = 0;
          rows[j].isFirstForTitle = false;
        }
      }

      if (row) {
        currentTitle = row.title;
        groupStart = i;
      }
    }
  }

  return rows;
}

function getStatusStyle(status: string) {
  switch (status) {
    case "broken":
      return { backgroundColor: "#CBCBCB", color: "#020617" };
    case "incomplete":
      return { backgroundColor: "#D37ABC", color: "#020617" };
    case "unmuxed":
      return { backgroundColor: "#FFE89A", color: "#020617" };
    case "not_nyaa":
      return { backgroundColor: "#639AFF", color: "#020617" };
    default:
      return {};
  }
}

function renderComparison(comparison: string) {
  const text = (comparison || "").trim();
  if (!text) {
    return <span className="text-slate-500">—</span>;
  }

  const lines = text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  return (
    <div className="space-y-1 break-words">
      {lines.map((line, idx) => {
        const isUrl = line.startsWith("http://") || line.startsWith("https://");
        if (!isUrl) {
          return (
            <div key={idx} className="text-xs text-slate-200 break-words">
              {line}
            </div>
          );
        }
        return (
          <div key={idx} className="text-xs break-words">
            <a
              href={line}
              className="text-indigo-300 underline hover:text-indigo-200 break-words whitespace-normal"
              target="_blank"
              rel="noreferrer"
            >
              {line}
            </a>
          </div>
        );
      })}
    </div>
  );
}

export default function Index() {
  const entries = releases as ReleaseEntry[];
  const rows = flattenToRows(entries);

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="w-full px-4 py-4">
        <h1 className="mb-4 text-3xl font-bold tracking-tight">StaticDex</h1>
        <div className="overflow-y-auto rounded-lg border border-slate-800 bg-slate-900/60">
          <table className="min-w-full table-fixed text-left text-sm">
            <thead className="sticky top-0 z-10 bg-slate-900">
              <tr>
                <th className="w-[18%] px-3 py-2 border border-slate-800 font-semibold text-slate-200">
                  Title
                </th>
                <th className="w-[16%] px-3 py-2 border border-slate-800 font-semibold text-slate-200">
                  Alt Title
                </th>
                <th className="w-[18%] px-3 py-2 border border-slate-800 font-semibold text-slate-200">
                  Best Release
                </th>
                <th className="w-[18%] px-3 py-2 border border-slate-800 font-semibold text-slate-200">
                  Alt Release
                </th>
                <th className="w-[15%] px-3 py-2 border border-slate-800 font-semibold text-slate-200">
                  Comparison
                </th>
                <th className="w-[15%] px-3 py-2 border border-slate-800 font-semibold text-slate-200">
                  Notes
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, idx) => (
                <tr
                  key={`${row.title}-${idx}`}
                  className={idx % 2 === 0 ? "bg-slate-900/60" : "bg-slate-900/30"}
                >
                  {row.isFirstForTitle && row.rowSpan > 0 && (
                    <>
                      <td
                        className="px-3 py-2 align-top border border-slate-800 break-words"
                        rowSpan={row.rowSpan}
                      >
                        {row.title}
                      </td>
                      <td
                        className="px-3 py-2 align-top border border-slate-800 text-slate-300 break-words"
                        rowSpan={row.rowSpan}
                      >
                        {row.alt_title || "—"}
                      </td>
                    </>
                  )}
                  <td
                    className={`px-3 py-2 align-top border border-slate-800 ${
                      row.best_status ? "text-black font-semibold" : "font-semibold text-slate-50"
                    } break-words`}
                    style={row.best_status ? getStatusStyle(row.best_status) : undefined}
                  >
                    {row.best_name || "—"}
                  </td>
                  <td
                    className={`px-3 py-2 align-top border border-slate-800 ${
                      row.alt_status ? "text-black font-semibold" : "font-semibold text-slate-50"
                    } break-words`}
                    style={row.alt_status ? getStatusStyle(row.alt_status) : undefined}
                  >
                    {row.alt_name || "—"}
                  </td>
                  {row.isFirstForTitle && row.rowSpan > 0 && (
                    <>
                      <td
                        className="px-3 py-2 align-top border border-slate-800 max-w-[15ch] break-words"
                        rowSpan={row.rowSpan}
                      >
                        {renderComparison(row.comparison)}
                      </td>
                      <td
                        className="px-3 py-2 align-top border border-slate-800 text-xs text-slate-300 max-w-[20ch] break-words whitespace-pre-wrap"
                        rowSpan={row.rowSpan}
                      >
                        {row.notes || "—"}
                      </td>
                    </>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </main>
  );
}
