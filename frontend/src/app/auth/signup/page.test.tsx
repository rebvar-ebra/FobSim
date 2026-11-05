import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import SignupPage from "./page";

const replace = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace }),
}));

describe("SignupPage", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    replace.mockReset();
    localStorage.clear();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ access_token: "new-user-token" }),
      }),
    );
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it("confirms registration before redirecting to the home page", async () => {
    render(<SignupPage />);

    fireEvent.change(screen.getByPlaceholderText("Full Name"), {
      target: { value: "Research User" },
    });
    fireEvent.change(screen.getByPlaceholderText("Email Address"), {
      target: { value: "researcher@example.com" },
    });
    fireEvent.change(screen.getByPlaceholderText("Password"), {
      target: { value: "secure-password" },
    });
    fireEvent.click(screen.getByRole("button", { name: /sign up/i }));

    await act(async () => {
      await Promise.resolve();
    });
    expect(screen.getByRole("status")).toHaveTextContent(
      "Registration successful",
    );
    expect(localStorage.getItem("token")).toBe("new-user-token");
    expect(replace).not.toHaveBeenCalled();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(1500);
    });

    expect(replace).toHaveBeenCalledWith("/");
  });
});
