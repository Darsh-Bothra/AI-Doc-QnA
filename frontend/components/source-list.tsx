import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import type { SearchHit } from "@/lib/types"

export function SourceList({ sources }: { sources: SearchHit[] }) {
  if (sources.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No sources were returned for this query.
      </p>
    )
  }

  return (
    <ScrollArea className="h-[min(28rem,60vh)]">
      <ol className="space-y-3 pr-3">
        {sources.map((source, index) => (
          <li
            key={`${source.chunk_id}-${index}`}
            className="rounded-lg border border-border bg-card p-3"
          >
            <div className="mb-2 flex items-center justify-between gap-2">
              <span className="text-xs font-medium text-muted-foreground">
                Source {index + 1}
              </span>
              <Badge variant="secondary" className="font-mono">
                {source.score.toFixed(3)}
              </Badge>
            </div>
            <p className="whitespace-pre-wrap text-sm leading-relaxed text-foreground/90">
              {source.text ?? "No text available."}
            </p>
          </li>
        ))}
      </ol>
    </ScrollArea>
  )
}
