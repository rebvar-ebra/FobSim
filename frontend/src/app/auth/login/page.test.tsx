import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import LoginPage from "./page";

const push = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

describe("LoginPage", () => {
  beforeEach(() => {
    push.mockReset();
    localStorage.clear();
    window.history.replaceState(null, "", "/auth/login");
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("offers a password recovery link", () => {
    render(<LoginPage />);

    expect(
      screen.getByRole("link", { name: /forgot password/i }),
    ).toHaveAttribute("href", "/auth/forgot-password");
  });

  it("returns the user to the protected page after login", async () => {
    window.history.replaceState(null, "", "/auth/login?next=%2Fsimulate");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ access_token: "session-token" }),
      }),
    );
    render(<LoginPage />);

    fireEvent.change(screen.getByPlaceholderText("Email Address"), {
      target: { value: "ada@example.com" },
    });
    fireEvent.change(screen.getByPlaceholderText("Password"), {
      target: { value: "secure-password" },
    });
    fireEvent.click(screen.getByRole("button", { name: /log in/i }));

    await act(async () => {
      await Promise.resolve();
    });

    expect(push).toHaveBeenCalledWith("/simulate");
  });
});
