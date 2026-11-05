import { act, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import RequireAuth from "./RequireAuth";

const replace = vi.fn();

vi.mock("next/navigation", () => ({
  usePathname: () => "/simulate",
  useRouter: () => ({ replace }),
}));

describe("RequireAuth", () => {
  beforeEach(() => {
    replace.mockReset();
    localStorage.clear();
  });

  it("hides protected content and sends guests to login", async () => {
    await act(async () => {
      render(<RequireAuth><div>Simulation controls</div></RequireAuth>);
      await Promise.resolve();
    });

    expect(screen.queryByText("Simulation controls")).not.toBeInTheDocument();
    expect(replace).toHaveBeenCalledWith("/auth/login?next=%2Fsimulate");
  });

  it("shows protected content when a login token exists", async () => {
    localStorage.setItem("token", "valid-session-token");

    await act(async () => {
      render(<RequireAuth><div>Simulation controls</div></RequireAuth>);
      await Promise.resolve();
    });

    expect(screen.getByText("Simulation controls")).toBeInTheDocument();
    expect(replace).not.toHaveBeenCalled();
  });
});
