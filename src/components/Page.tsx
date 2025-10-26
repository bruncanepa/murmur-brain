import { ReactNode } from 'react';

interface PageProps {
  title?: string;
  subtitle?: string;
  children: ReactNode;
  maxWidth?: string;
}

function Page({ title, subtitle, children, maxWidth = '7xl' }: PageProps) {
  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
      <div className={`max-w-${maxWidth} mx-auto px-6 py-8`}>
        {(title || subtitle) && (
          <div className="mb-6">
            {title && (
              <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                {title}
              </h1>
            )}
            {subtitle && (
              <p className="mt-2 text-gray-600 dark:text-gray-400">
                {subtitle}
              </p>
            )}
          </div>
        )}
        {children}
      </div>
    </div>
  );
}

export default Page;
