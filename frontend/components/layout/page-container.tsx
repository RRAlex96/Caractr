import { cn } from "@/lib/utils"

interface PageContainerProps {
  children: React.ReactNode
  className?: string
  /** Max width variant */
  size?: "sm" | "md" | "lg" | "full"
  /** Add top padding for navbar clearance */
  padNav?: boolean
}

const sizeClasses = {
  sm: "max-w-2xl",    // 672px — single column content (analysis, wizard)
  md: "max-w-4xl",    // 896px — medium content
  lg: "max-w-7xl",    // 1280px — wide content (results grid)
  full: "max-w-none", // Full width
}

export function PageContainer({
  children,
  className,
  size = "lg",
  padNav = true,
}: PageContainerProps) {
  return (
    <div
      className={cn(
        "mx-auto w-full px-6 lg:px-8",
        sizeClasses[size],
        padNav && "pt-16",
        className
      )}
    >
      {children}
    </div>
  )
}
