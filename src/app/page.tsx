"use client";

import { useState, useEffect } from "react";
import releases from "../../data/releases.json";
import { Sun, Moon } from "lucide-react";

type ReleaseEntry = {
  title: string;
  alt_title: string;
  year: number | null;
  format: string | null;
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
  year: number | null;
  format: string | null;
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
        year: entry.year,
        format: entry.format,
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

function renderComparison(comparison: string, theme: "light" | "dark") {
  const text = (comparison || "").trim();
  if (!text) return <span className="text-slate-500 dark:text-slate-300">—</span>;

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
            <div
              key={idx}
              className={`text-xs break-words ${theme === "dark" ? "text-slate-300" : "text-black"
                }`}
            >
              {line}
            </div>
          );
        }
        return (
          <div key={idx} className="text-xs break-words">
            <a
              href={line}
              className="text-indigo-600 dark:text-indigo-300 underline hover:text-indigo-500 dark:hover:text-indigo-200 break-words whitespace-normal"
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

function formatMediaType(format: string | null): string {
  if (!format) return '';

  const formatMap: { [key: string]: string } = {
    'TV': 'TV',
    'MOVIE': 'Movie',
    'OVA': 'OVA',
    'SPECIAL': 'Special',
    'ONA': 'ONA',
    'TV_SHORT': 'TV Short'
  };

  return formatMap[format] || format;
}

export default function Index() {
  const [theme, setTheme] = useState<"light" | "dark">("dark");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem("theme");
    if (saved === "light" || saved === "dark") setTheme(saved);
    setMounted(true); // now we know theme for sure
  }, []);

  const toggleTheme = () => {
    setTheme((prev) => {
      const next = prev === "dark" ? "light" : "dark";
      localStorage.setItem("theme", next);
      return next;
    });
  };

  if (!mounted) return null;

  const entries = releases as ReleaseEntry[];
  const rows = flattenToRows(entries);

  return (
    <main
      className={`min-h-screen ${theme === "dark" ? "bg-slate-950 text-slate-300" : "bg-white text-black"
        }`}
    >
      <div className="w-full px-4 py-4">
        <div className="flex justify-between items-center mb-4">
          <h1 className="text-3xl font-bold tracking-tight">StaticDex</h1>
          <button
            onClick={toggleTheme}
            className="w-10 h-10 flex items-center justify-center rounded-md }"
          >
            {theme === "dark" ? (
              <Sun size={24} className="text-slate-300" />
            ) : (
              <Moon size={24} className="text-black" />
            )}
          </button>
        </div>

        <table className="min-w-full table-fixed text-left text-sm border-collapse">
          <thead className={`sticky top-0 z-10 ${theme === "dark" ? "bg-slate-900" : "bg-slate-200"} text-lg`}>
            <tr className="border-slate-400 dark:border-slate-800">
              <th className={`w-[20%] px-3 py-2 border ${theme === "dark" ? "border-slate-800" : "border-slate-400"} font-bold`}>Title</th>
              <th className={`w-[20%] px-3 py-2 border ${theme === "dark" ? "border-slate-800" : "border-slate-400"} font-bold`}>Alt Title</th>
              <th className={`w-[15%] px-3 py-2 border ${theme === "dark" ? "border-slate-800" : "border-slate-400"} font-bold`}>Best Release</th>
              <th className={`w-[15%] px-3 py-2 border ${theme === "dark" ? "border-slate-800" : "border-slate-400"} font-bold`}>Alt Release</th>
              <th className={`w-[15%] px-3 py-2 border ${theme === "dark" ? "border-slate-800" : "border-slate-400"} font-bold`}>Comparison</th>
              <th className={`w-[15%] px-3 py-2 border ${theme === "dark" ? "border-slate-800" : "border-slate-400"} font-bold`}>Notes</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, idx) => (
              <tr
                key={`${row.title}-${idx}`}
                className={
                  idx % 2 === 0
                    ? theme === "dark" ? "bg-slate-900/60" : "bg-slate-200/60"
                    : theme === "dark" ? "bg-slate-900/30" : "bg-slate-100/30"
                }
              >
                {row.isFirstForTitle && row.rowSpan > 0 && (
                  <>
                    <td
                      rowSpan={row.rowSpan}
                      className={`px-3 py-2 align-top border ${theme === "dark" ? "border-slate-800" : "border-slate-400"}`}
                    >
                      <div className="flex flex-wrap items-center gap-1">
                        {row.title}
                        {row.year ? <span className="font-bold"> ({row.year})</span> : ''}
                        {row.format ? <span className="ml-0.5 text-xs px-2 py-0.5 rounded-full bg-slate-700 text-slate-300">
                          {formatMediaType(row.format)}
                        </span> : ''}
                      </div>
                    </td>
                    <td
                      rowSpan={row.rowSpan}
                      className={`px-3 py-2 align-top border ${theme === "dark" ? "border-slate-800" : "border-slate-400"} break-words ${theme === "dark" ? "text-slate-300" : "text-black"
                        }`}
                    >
                      {row.alt_title || "—"}
                    </td>
                  </>
                )}
                <td
                  className={`px-3 py-2 align-top border ${theme === "dark" ? "border-slate-800" : "border-slate-400"} break-words font-semibold`}
                  style={row.best_status ? getStatusStyle(row.best_status) : undefined}
                >
                  {row.best_name || "—"}
                </td>
                <td
                  className={`px-3 py-2 align-top border ${theme === "dark" ? "border-slate-800" : "border-slate-400"} break-words font-semibold`}
                  style={row.alt_status ? getStatusStyle(row.alt_status) : undefined}
                >
                  {row.alt_name || "—"}
                </td>
                {row.isFirstForTitle && row.rowSpan > 0 && (
                  <>
                    <td
                      rowSpan={row.rowSpan}
                      className={`px-3 py-2 align-top border ${theme === "dark" ? "border-slate-800" : "border-slate-400"} max-w-[15ch] break-words`}
                    >
                      {renderComparison(row.comparison, theme)}
                    </td>
                    <td
                      rowSpan={row.rowSpan}
                      className={`px-3 py-2 align-top border ${theme === "dark" ? "border-slate-800" : "border-slate-400"} max-w-[20ch] break-words whitespace-pre-wrap ${theme === "dark" ? "text-slate-300" : "text-black"
                        }`}
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
    </main>
  );
}
