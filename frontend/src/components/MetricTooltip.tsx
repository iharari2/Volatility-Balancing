import { HelpCircle } from 'lucide-react';

export default function MetricTooltip({ text }: { text: string }) {
  return (
    <span className="group relative inline-flex ml-1 cursor-help align-middle">
      <HelpCircle className="h-3.5 w-3.5 text-gray-400 group-hover:text-gray-600 transition-colors" />
      <span className="pointer-events-none absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 w-52 rounded-lg bg-gray-900 px-2.5 py-1.5 text-xs text-white leading-snug opacity-0 group-hover:opacity-100 transition-opacity z-50 shadow-lg whitespace-normal text-center">
        {text}
        <span className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900" />
      </span>
    </span>
  );
}
