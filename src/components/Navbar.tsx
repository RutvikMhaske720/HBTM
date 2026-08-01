import Link from "next/link";
import { Caveat } from "next/font/google";

const signature = Caveat({ subsets: ["latin"], weight: "600" });

const NAV_LINKS = [
  { label: "How it works?", href: "/#how-it-works" },
  { label: "IABTM Podcast", href: "/podcast" },
  { label: "Experts", href: "/experts" },
  { label: "Artists", href: "/artists" },
];

export default function Navbar() {
  return (
    <header className="sticky top-0 z-50 border-b border-(--color-border) bg-(--color-bg-primary)/90 backdrop-blur">
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4 lg:px-10">
        <Link href="/" className="flex flex-col leading-none">
          <span className="font-display text-2xl font-semibold tracking-tight text-(--color-ink)">
            IABTM
          </span>
          <span className="mt-0.5 text-[9px] font-medium tracking-[0.2em] text-(--color-text-tertiary)">
            I AM BETTER THAN ME
          </span>
        </Link>

        <div className="hidden items-center gap-9 md:flex">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.label}
              href={link.href}
              className="text-[15px] text-(--color-ink-soft) transition-colors hover:text-(--color-accent-secondary)"
            >
              {link.label}
            </Link>
          ))}
          <Link
            href="/community"
            className={`${signature.className} text-2xl text-(--color-accent-secondary)`}
          >
            3605
          </Link>
          <Link
            href="/shop"
            className="text-[15px] text-(--color-ink-soft) transition-colors hover:text-(--color-accent-secondary)"
          >
            Shop
          </Link>
        </div>

        <Link
          href="/auth"
          className="rounded-full bg-(--color-accent-secondary) px-6 py-2.5 text-[15px] font-medium text-(--color-text-inverse) transition-transform hover:-translate-y-0.5 hover:brightness-110"
        >
          Sign in
        </Link>
      </nav>
    </header>
  );
}
