import { ReactNode } from 'react';

interface PageProps {
  title: string;
  subtitle: string;
  children: ReactNode;
  maxWidth?: string;
  className?: string;
}

function Page({ title, subtitle, children, className }: PageProps) {
  return (
    <div
      className={`bg-gray-100 dark:bg-gray-900 w-full h-full p-6 flex flex-col ${className}`}
    >
      {/* Fixed Header */}
      <div className="flex-shrink-0 mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
          {title}
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">{subtitle}</p>
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto rounded-lg">{children}</div>
    </div>
  );
}

export default Page;
