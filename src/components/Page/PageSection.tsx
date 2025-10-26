import { ReactNode } from 'react';

interface PageSectionProps {
  title: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}

/**
 * Generic page section component with consistent styling
 * Matches the pattern used in Settings page sections
 */
export default function PageSection({
  title,
  action,
  children,
  className = '',
}: PageSectionProps) {
  return (
    <div className={`${className} mt-6`}>
      {/* Section Header */}
      <div className="flex justify-between items-center mb-4 px-1">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          {title}
        </h2>
        {action && <div>{action}</div>}
      </div>

      {/* Section Content Card */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
        {children}
      </div>
    </div>
  );
}
