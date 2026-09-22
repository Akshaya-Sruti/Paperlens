import { useState } from "react";
import { Link, NavLink } from "react-router-dom";
import { cx } from "../../lib/utils";
import { BrandMark } from "../ui/BrandMark";
import { Button } from "../ui/Button";

const links = [
  { to: "/#how-it-works", label: "How it works", hash: true },
  { to: "/#features", label: "Features", hash: true },
];

export function Navbar() {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 border-b border-line bg-paper/95 backdrop-blur-[2px]">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-5">
        <Link
          to="/"
          className="flex items-center gap-2.5"
          aria-label="PaperLens home"
        >
          <BrandMark size={26} />
          <span className="text-[15px] font-semibold tracking-tight">
            PaperLens
          </span>
        </Link>

        <nav
          className="hidden items-center gap-7 md:flex"
          aria-label="Primary"
        >
          <a
            href="#how-it-works"
            className="text-sm text-secondary transition-colors hover:text-ink"
          >
            How it works
          </a>
          <a
            href="#features"
            className="text-sm text-secondary transition-colors hover:text-ink"
          >
            Features
          </a>
          <NavLink
            to="/workspace"
            className={({ isActive }) =>
              cx(
                "text-sm transition-colors hover:text-ink",
                isActive ? "text-ink" : "text-secondary",
              )
            }
          >
            Workspace
          </NavLink>
        </nav>

        <div className="hidden md:block">
          <Link to="/upload">
            <Button size="sm">Upload paper</Button>
          </Link>
        </div>

        <button
          type="button"
          className="flex h-9 w-9 items-center justify-center rounded-[4px] border border-line bg-surface md:hidden"
          aria-expanded={open}
          aria-label={open ? "Close menu" : "Open menu"}
          onClick={() => setOpen((v) => !v)}
        >
          <span aria-hidden="true" className="text-lg leading-none">
            {open ? "×" : "≡"}
          </span>
        </button>
      </div>

      {open ? (
        <nav
          className="border-t border-line bg-surface px-5 py-3 md:hidden"
          aria-label="Mobile"
        >
          <ul className="flex flex-col gap-1">
            {links.map((l) => (
              <li key={l.label}>
                <a
                  href={l.to.replace("/", "")}
                  onClick={() => setOpen(false)}
                  className="block rounded-[4px] px-2 py-2 text-sm text-ink hover:bg-muted"
                >
                  {l.label}
                </a>
              </li>
            ))}
            <li>
              <Link
                to="/workspace"
                onClick={() => setOpen(false)}
                className="block rounded-[4px] px-2 py-2 text-sm text-ink hover:bg-muted"
              >
                Workspace
              </Link>
            </li>
            <li className="pt-2">
              <Link to="/upload" onClick={() => setOpen(false)}>
                <Button size="sm" className="w-full">
                  Upload paper
                </Button>
              </Link>
            </li>
          </ul>
        </nav>
      ) : null}
    </header>
  );
}
