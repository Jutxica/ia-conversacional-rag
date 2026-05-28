import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ExternalLink, FileText } from 'lucide-react'
import { cn } from '@/lib/utils'
import { motion } from 'framer-motion'

interface Citation {
  id: string | number
  title: string
  sigla?: string
  snippet?: string
  score?: number
  rerank_score?: number
  destinatario?: string
  data?: string
  page_url?: string
  page_number?: string | number
}

interface CitationGridProps {
  citations: Citation[]
  variant?: 'grid' | 'sidebar'
}

const scoreColor = (score: number = 0) => {
  if (score >= 0.8) return 'text-emerald-500 dark:text-emerald-400'
  if (score >= 0.55) return 'text-amber-500 dark:text-amber-400'
  return 'text-zinc-500 dark:text-zinc-400'
}

const scoreBg = (score: number = 0) => {
  if (score >= 0.8) return 'bg-emerald-500/10 border-emerald-500/20'
  if (score >= 0.55) return 'bg-amber-500/10 border-amber-500/20'
  return 'bg-zinc-500/10 border-zinc-500/20'
}

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
}

const itemVariants = {
  hidden: { opacity: 0, y: 20, scale: 0.95 },
  show: { 
    opacity: 1, 
    y: 0, 
    scale: 1,
    transition: {
      type: "spring",
      stiffness: 100,
      damping: 15
    }
  }
}

const safeRender = (val: any): string => {
  if (val === null || val === undefined) return '';
  if (Array.isArray(val)) {
    return val.map(safeRender).join(', ');
  }
  if (typeof val === 'object') {
    if (val.name && typeof val.name === 'string') return val.name;
    if (val.title && typeof val.title === 'string') return val.title;
    try {
      return JSON.stringify(val);
    } catch {
      return '';
    }
  }
  return String(val);
};

export default function CitationGrid({ citations, variant = 'grid' }: CitationGridProps) {
  if (!citations || citations.length === 0) return null

  const sorted = [...citations].sort((a, b) => (b.score || 0) - (a.score || 0))

  return (
    <motion.div 
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className={cn(
        "grid gap-4",
        variant === 'grid' 
          ? "grid-cols-1 md:grid-cols-4 auto-rows-[minmax(180px,auto)] p-4" 
          : "grid-cols-1 auto-rows-auto p-1"
      )}
    >
      {sorted.map((citation, idx) => {
        // Bento grid sizing logic only for grid variant
        const isFeatured = variant === 'grid' && idx === 0 && sorted.length >= 2;
        const isWide = variant === 'grid' && ((idx === 1 || idx === 2) && sorted.length >= 3);
        
        return (
          <motion.div
            key={citation.id ?? idx}
            variants={itemVariants}
            className={cn(
              "flex",
              variant === 'grid' && isFeatured && "md:col-span-2 md:row-span-2",
              variant === 'grid' && isWide && "md:col-span-2",
              variant === 'grid' && !isFeatured && !isWide && "md:col-span-1",
              variant === 'sidebar' && "col-span-1"
            )}
          >
            <Card
              className={cn(
                'group cursor-pointer transition-all duration-500 flex flex-col w-full h-full overflow-hidden relative',
                'hover:-translate-y-1 hover:shadow-xl hover:shadow-primary/5',
                variant === 'grid'
                  ? 'bg-card/80 backdrop-blur-sm border-border/50 hover:border-primary/40'
                  : 'bg-card/40 backdrop-blur-md border-border/40 hover:border-amber-500/40 dark:hover:border-amber-400/40 shadow-sm',
                isFeatured && 'bg-gradient-to-br from-card to-primary/5'
              )}
              onClick={() => citation.page_url && window.open(citation.page_url, '_blank')}
            >
              <CardHeader className="flex-row items-start justify-between gap-2 pb-2">
                <div className="flex items-center gap-2 min-w-0">
                  <Badge variant="outline" className={cn(
                    "font-mono text-[10px] tracking-wider uppercase shrink-0 transition-colors",
                    "group-hover:border-primary/30 group-hover:bg-primary/5"
                  )}>
                    {safeRender(citation.sigla) || 'DOC'}
                  </Badge>
                  <span className={cn('text-[11px] font-bold', scoreColor(citation.score))}>
                    {Math.round((citation.score || 0) * 100)}%
                  </span>
                </div>
                <div className={cn('px-1.5 py-0.5 rounded text-[10px] font-medium border backdrop-blur-md', scoreBg(citation.rerank_score ?? citation.score))}>
                  {citation.rerank_score != null ? 'Re-rankeado' : 'Similaridade'}
                </div>
              </CardHeader>

              <CardContent className="space-y-3 flex-grow flex flex-col justify-between">
                <div>
                  <CardTitle className={cn(
                    "font-display leading-tight line-clamp-2 text-foreground/90 transition-colors group-hover:text-primary",
                    isFeatured ? "text-lg md:text-xl mb-3" : "text-sm mb-2",
                    variant === 'sidebar' && "text-[13px] font-semibold"
                  )}>
                    {safeRender(citation.title) || 'Documento Dehoniano'}
                  </CardTitle>

                  {citation.snippet && (
                    <div className={cn(
                      "pl-3 border-l-2 border-amber-500/40 dark:border-amber-400/30",
                      variant === 'sidebar' ? "my-2" : "my-1"
                    )}>
                      <p className={cn(
                        "text-muted-foreground/80 leading-relaxed font-serif italic",
                        variant === 'sidebar'
                          ? "text-[12.5px] line-clamp-5"
                          : isFeatured ? "text-sm line-clamp-6" : "text-xs line-clamp-3"
                      )}>
                        &ldquo;{safeRender(citation.snippet)}&rdquo;
                      </p>
                    </div>
                  )}
                </div>

                <div className="flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-muted-foreground/70 font-medium pt-2 border-t border-border/30">
                  {citation.destinatario && (
                    <span className="truncate max-w-[140px] flex items-center gap-1">
                      <span className="w-1 h-1 rounded-full bg-primary/40"></span>
                      Para: {safeRender(citation.destinatario)}
                    </span>
                  )}
                  {citation.data && (
                    <span className="flex items-center gap-1">
                      <span className="w-1 h-1 rounded-full bg-secondary/40"></span>
                      {safeRender(citation.data)}
                    </span>
                  )}
                  {citation.page_number && (
                    <span className="flex items-center gap-1">
                      <span className="w-1 h-1 rounded-full bg-accent/40"></span>
                      p. {safeRender(citation.page_number)}
                    </span>
                  )}
                </div>
              </CardContent>

              <CardFooter className="justify-between text-[11px] text-muted-foreground/50 py-3 bg-muted/20 mt-auto border-t border-border/10">
                <span className="flex items-center gap-1.5 font-medium transition-colors group-hover:text-primary/70">
                  <FileText className="size-3.5" />
                  Visualizar documento
                </span>
                <ExternalLink className="size-3.5 opacity-0 -translate-x-2 transition-all duration-300 group-hover:opacity-100 group-hover:translate-x-0 group-hover:text-primary" />
              </CardFooter>
              
              {/* Highlight gradient on hover */}
              <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-transparent to-primary/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
            </Card>
          </motion.div>
        )
      })}
    </motion.div>
  )
}
