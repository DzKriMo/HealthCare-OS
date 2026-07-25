/**
 * Shared icon components.
 */
import {
  Stethoscope,
  Calendar,
  Users,
  FileText,
  CreditCard,
  Bell,
  BarChart3,
  Shield,
  Settings,
  LogOut,
  Menu,
  X,
  ChevronDown,
  Search,
  Plus,
  MoreHorizontal,
  Activity,
  Download,
  Pill,
  AlertTriangle,
  HeartPulse,
  Syringe,
  type LucideIcon,
} from "lucide-react";

export type IconName = keyof typeof iconMap;

const iconMap = {
  stethoscope: Stethoscope,
  calendar: Calendar,
  users: Users,
  fileText: FileText,
  creditCard: CreditCard,
  bell: Bell,
  barChart: BarChart3,
  shield: Shield,
  settings: Settings,
  logOut: LogOut,
  menu: Menu,
  x: X,
  chevronDown: ChevronDown,
  search: Search,
  plus: Plus,
  moreHorizontal: MoreHorizontal,
  activity: Activity,
  download: Download,
  pill: Pill,
  alertTriangle: AlertTriangle,
  heartPulse: HeartPulse,
  syringe: Syringe,
};

function Logo({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M12 2L2 7l10 5 10-5-10-5z" />
      <path d="M2 17l10 5 10-5" />
      <path d="M2 12l10 5 10-5" />
    </svg>
  );
}

function createIcon(Icon: LucideIcon) {
  const IconWrapper = ({ className }: { className?: string }) => (
    <Icon className={className} />
  );
  IconWrapper.displayName = "Icon";
  return IconWrapper;
}

export const Icons = {
  logo: Logo,
  ...Object.fromEntries(
    Object.entries(iconMap).map(([name, icon]) => [name, createIcon(icon)]),
  ) as unknown as Record<IconName, ({ className }: { className?: string }) => JSX.Element>,
};
