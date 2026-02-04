import releases from "../../data/releases.json";

type Release = {
  title: string;
  alt_title: string;
  notes: string;
  comparison: string;
  best_release: string;
  alt_release: string;
  best_status: string;
  alt_status: string;
};

export default function Index() {
  const data = releases as Release[];

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-6xl px-4 py-8">
        <h1 className="mb-6 text-3xl font-bold tracking-tight">StaticDex Releases</h1>
        <p className="mb-6 text-sm text-slate-300">
          Simple static table rendered from <code>data/releases.json</code>.
        </p>
        <div className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-900/60">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-slate-900">
              <tr>
                <th className="px-3 py-2 font-semibold text-slate-200">Title</th>
                <th className="px-3 py-2 font-semibold text-slate-200">Alt Title</th>
                <th className="px-3 py-2 font-semibold text-slate-200">Best Release</th>
                <th className="px-3 py-2 font-semibold text-slate-200">Alt Release</th>
                <th className="px-3 py-2 font-semibold text-slate-200">Comparison</th>
                <th className="px-3 py-2 font-semibold text-slate-200">Notes</th>
              </tr>
            </thead>
            <tbody>
              {data.map((item, idx) => (
                <tr
                  key={`${item.title}-${idx}`}
                  className={idx % 2 === 0 ? "bg-slate-900/60" : "bg-slate-900/30"}
                >
                  <td className="px-3 py-2 align-top">{item.title}</td>
                  <td className="px-3 py-2 align-top text-slate-300">
                    {item.alt_title || "\u2014"}
                  </td>
                  <td className="px-3 py-2 align-top text-emerald-300">
                    {item.best_release || "\u2014"}
                    {item.best_status && (
                      <span className="ml-1 text-xs text-emerald-400">
                        ({item.best_status})
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2 align-top text-sky-300">
                    {item.alt_release || "\u2014"}
                    {item.alt_status && (
                      <span className="ml-1 text-xs text-sky-400">
                        ({item.alt_status})
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2 align-top">
                    {item.comparison ? (
                      <a
                        href={item.comparison.split("\n")[0]}
                        className="text-xs text-indigo-300 underline hover:text-indigo-200"
                        target="_blank"
                        rel="noreferrer"
                      >
                        View
                      </a>
                    ) : (
                      <span className="text-slate-500">\u2014</span>
                    )}
                  </td>
                  <td className="px-3 py-2 align-top max-w-xs text-xs text-slate-300">
                    {item.notes || "\u2014"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </main>
  );
}
