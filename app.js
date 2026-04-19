/* ===========================================================
   NovaBank — app.js  (Flask API version)
   All data is saved to PostgreSQL via Flask endpoints.
   =========================================================== */

(() => {
  "use strict";

  // ---------- Session (in-memory only) ----------
  const State = { currentUser: null }; // { account_number, name, balance, pin }

  // ---------- API helper ----------
  const BASE_URL = "https://banking-system-wlc3.onrender.com";

  async function api(path, body = null) {
    const opts = body
      ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }
      : { method: "GET" };
    const res = await fetch(BASE_URL + path, opts);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Request failed.");
    return data;
  }

  // ---------- DOM helpers ----------
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  const fmtMoney = (n) =>
    Number(n || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  const fmtTime = (str) => {
    const d = new Date(str);
    if (isNaN(d.getTime())) return str;
    return d.toLocaleString(undefined, {
      year: "numeric", month: "short", day: "2-digit",
      hour: "2-digit", minute: "2-digit",
    });
  };

  // ---------- Toasts ----------
  const toast = (message, variant = "info") => {
    const root = $("#toastRoot");
    const el = document.createElement("div");
    el.className = `toast toast--${variant}`;
    el.innerHTML = `<span class="dot"></span><span>${message}</span>`;
    root.appendChild(el);
    setTimeout(() => {
      el.classList.add("leaving");
      el.addEventListener("animationend", () => el.remove(), { once: true });
    }, 2600);
  };

  // ---------- Balance count-up ----------
  let _raf = null;
  const animateBalance = (to, from = 0, duration = 900) => {
    const el = $("#balanceDisplay");
    if (!el) return;
    cancelAnimationFrame(_raf);
    const start = performance.now();
    const ease = (t) => 1 - Math.pow(1 - t, 3);
    const step = (now) => {
      const t = Math.min(1, (now - start) / duration);
      el.textContent = fmtMoney(from + (to - from) * ease(t));
      if (t < 1) _raf = requestAnimationFrame(step);
    };
    _raf = requestAnimationFrame(step);
  };

  // ---------- Screens ----------
  const showAuth = () => {
    $("#authScreen").classList.remove("hidden");
    $("#dashboard").classList.add("hidden");
    $("#adminScreen").classList.add("hidden");
    $("#navLogoutBtn").classList.add("hidden");
    $("#navLogoutBtn").classList.remove("inline-flex");
    $("#navAdminBtn").classList.remove("hidden");
    State.currentUser = null;
  };

  const showDashboard = () => {
    $("#authScreen").classList.add("hidden");
    $("#dashboard").classList.remove("hidden");
    $("#adminScreen").classList.add("hidden");
    $("#navLogoutBtn").classList.remove("hidden");
    $("#navLogoutBtn").classList.add("inline-flex");
    $("#navAdminBtn").classList.remove("hidden");
    renderDashboard();
  };

  const showAdmin = async () => {
    $("#authScreen").classList.add("hidden");
    $("#dashboard").classList.add("hidden");
    $("#adminScreen").classList.remove("hidden");
    await renderAdmin();
  };

  // ---------- Dashboard ----------
  const renderDashboard = async (animate = true) => {
    const u = State.currentUser;
    if (!u) return;
    $("#userName").textContent = u.name;
    $("#userAcct").textContent = u.account_number;
    if (animate) animateBalance(u.balance, 0, 900);
    else $("#balanceDisplay").textContent = fmtMoney(u.balance);
    await renderTransactions();
  };

  const actionMeta = (action) => {
    const a = action.toLowerCase();
    if (a.includes("deposit")) return { sign: "+", cls: "amount-pos", color: "bg-emerald-brand/15 text-emerald-glow border-emerald-brand/30" };
    if (a.includes("withdraw")) return { sign: "-", cls: "amount-neg", color: "bg-rose-brand/15 text-rose-glow border-rose-brand/30" };
    if (a.includes("created")) return { sign: "", cls: "text-muted", color: "bg-emerald-brand/10 text-emerald-glow border-emerald-brand/20" };
    if (a.includes("deleted")) return { sign: "", cls: "text-muted", color: "bg-rose-brand/10 text-rose-glow border-rose-brand/20" };
    return { sign: "", cls: "text-muted", color: "bg-white/5 text-white/80 border-line" };
  };

  const renderTransactions = async () => {
    if (!State.currentUser) return;
    try {
      const { logs } = await api("/api/transactions", { account_number: State.currentUser.account_number });
      const search = ($("#txSearch").value || "").toLowerCase().trim();
      const filtered = logs.filter(l =>
        !search ||
        l.action.toLowerCase().includes(search) ||
        String(l.amount).includes(search) ||
        (l.timestamp || "").toLowerCase().includes(search)
      );
      const tbody = $("#txTable");
      tbody.innerHTML = "";
      if (!filtered.length) { $("#txEmpty").classList.remove("hidden"); return; }
      $("#txEmpty").classList.add("hidden");
      for (const log of filtered) {
        const meta = actionMeta(log.action);
        const tr = document.createElement("tr");
        tr.className = "tx-row";
        tr.innerHTML = `
          <td class="px-5 py-3 font-mono text-xs text-muted">#${log.id}</td>
          <td class="px-5 py-3">
            <span class="inline-flex items-center gap-2 px-2.5 py-1 rounded-md text-xs font-medium border ${meta.color}">
              ${log.action}
            </span>
          </td>
          <td class="px-5 py-3 text-right font-medium tabular-nums ${meta.cls}">
            ${log.amount > 0 ? `${meta.sign}$${fmtMoney(log.amount)}` : "—"}
          </td>
          <td class="px-5 py-3 text-muted text-xs">${fmtTime(log.timestamp)}</td>`;
        tbody.appendChild(tr);
      }
    } catch (e) { console.error("Transactions error:", e); }
  };

  // ---------- Admin ----------
  const renderAdmin = async () => {
    try {
      const [{ logs }, stats] = await Promise.all([
        api("/api/admin/logs"),
        api("/api/admin/stats"),
      ]);
      $("#statAccounts").textContent = stats.total_accounts;
      $("#statDeposits").textContent = `$${fmtMoney(stats.total_deposits)}`;
      $("#statWithdrawals").textContent = `$${fmtMoney(stats.total_withdrawals)}`;

      const search = ($("#adminSearch").value || "").toLowerCase().trim();
      const filtered = logs.filter(l =>
        !search ||
        (l.account_number || "").toLowerCase().includes(search) ||
        (l.holder_name || "").toLowerCase().includes(search) ||
        (l.action || "").toLowerCase().includes(search)
      );
      const tbody = $("#adminTable");
      tbody.innerHTML = "";
      if (!filtered.length) { $("#adminEmpty").classList.remove("hidden"); return; }
      $("#adminEmpty").classList.add("hidden");
      for (const log of filtered) {
        const meta = actionMeta(log.action);
        const tr = document.createElement("tr");
        tr.className = "tx-row";
        tr.innerHTML = `
          <td class="px-5 py-3 font-mono text-xs text-muted">#${log.id}</td>
          <td class="px-5 py-3 font-mono text-xs">${log.account_number}</td>
          <td class="px-5 py-3">${log.holder_name}</td>
          <td class="px-5 py-3">
            <span class="inline-flex items-center gap-2 px-2.5 py-1 rounded-md text-xs font-medium border ${meta.color}">
              ${log.action}
            </span>
          </td>
          <td class="px-5 py-3 text-right font-medium tabular-nums ${meta.cls}">
            ${log.amount > 0 ? `${meta.sign}$${fmtMoney(log.amount)}` : "—"}
          </td>
          <td class="px-5 py-3 text-muted text-xs">${fmtTime(log.timestamp)}</td>`;
        tbody.appendChild(tr);
      }
    } catch (e) { console.error("Admin error:", e); }
  };

  // ---------- Modal ----------
  const openModal = (title, subtitle, bodyHTML, onMount) => {
    $("#modalTitle").textContent = title;
    $("#modalSubtitle").textContent = subtitle;
    $("#modalBody").innerHTML = bodyHTML;
    $("#modalRoot").classList.remove("hidden");
    document.body.style.overflow = "hidden";
    onMount?.();
  };
  const closeModal = () => {
    $("#modalRoot").classList.add("hidden");
    document.body.style.overflow = "";
  };

  // ---------- Amount modal (deposit / withdraw) ----------
  const openAmountModal = (kind) => {
    const isDeposit = kind === "deposit";
    openModal(
      isDeposit ? "Deposit funds" : "Withdraw funds",
      isDeposit ? "Add money to your account." : `Available: $${fmtMoney(State.currentUser.balance)}`,
      `<form id="amtForm" class="space-y-4">
        <div>
          <label class="text-xs font-medium text-muted uppercase tracking-wider">Amount (USD)</label>
          <div class="relative mt-1.5">
            <span class="absolute left-3 top-1/2 -translate-y-1/2 text-muted">$</span>
            <input name="amount" type="number" step="0.01" min="0.01" required autofocus
              class="input pl-7 text-lg font-semibold" placeholder="0.00" />
          </div>
        </div>
        <div class="flex flex-wrap gap-2">
          ${[10, 50, 100, 500].map(v => `<button type="button" data-quick="${v}" class="btn btn-ghost text-xs py-1.5 px-3">+$${v}</button>`).join("")}
        </div>
        <div class="flex gap-2 pt-2">
          <button type="button" data-close-modal class="btn btn-ghost flex-1">Cancel</button>
          <button type="submit" class="btn ${isDeposit ? "btn-primary" : "btn-danger"} flex-1">
            ${isDeposit ? "Deposit" : "Withdraw"}
          </button>
        </div>
      </form>`,
      () => {
        const form = $("#amtForm");
        const input = form.elements.amount;
        $$("[data-quick]", form).forEach(b =>
          b.addEventListener("click", () => {
            input.value = (parseFloat(input.value || "0") + parseFloat(b.dataset.quick)).toFixed(2);
            input.focus();
          })
        );
        form.addEventListener("submit", async (e) => {
          e.preventDefault();
          const amt = parseFloat(input.value);
          if (!amt || amt <= 0) return toast("Enter a valid amount.", "error");
          const btn = form.querySelector("[type=submit]");
          btn.disabled = true;
          try {
            const endpoint = isDeposit ? "/api/deposit" : "/api/withdraw";
            const data = await api(endpoint, {
              account_number: State.currentUser.account_number,
              pin: State.currentUser.pin,
              amount: amt,
            });
            const before = State.currentUser.balance;
            State.currentUser.balance = data.balance;
            closeModal();
            renderDashboard(false);
            animateBalance(data.balance, before, 700);
            toast(`${isDeposit ? "Deposited" : "Withdrew"} $${fmtMoney(amt)}`, "success");
          } catch (err) {
            toast(err.message, "error");
          } finally {
            btn.disabled = false;
          }
        });
      }
    );
  };

  // ---------- Settings modal ----------
  const openSettingsModal = () => {
    openModal(
      "Account settings",
      "Update your details or remove your account.",
      `<div class="space-y-5">
        <form id="nameForm" class="space-y-3">
          <label class="text-xs font-medium text-muted uppercase tracking-wider">Display name</label>
          <div class="flex gap-2">
            <input name="name" required value="${State.currentUser.name.replace(/"/g, "&quot;")}" class="input flex-1" />
            <button class="btn btn-primary px-4" type="submit">Save</button>
          </div>
        </form>
        <div class="h-px bg-line"></div>
        <form id="pinForm" class="space-y-3">
          <label class="text-xs font-medium text-muted uppercase tracking-wider">Change PIN</label>
          <input name="old_pin" type="password" inputmode="numeric" maxlength="4"
            placeholder="Current PIN" class="input tracking-[0.5em] text-center" required />
          <div class="grid grid-cols-2 gap-2">
            <input name="new_pin" type="password" inputmode="numeric" maxlength="4"
              placeholder="New PIN" class="input tracking-[0.5em] text-center" required />
            <input name="confirm_pin" type="password" inputmode="numeric" maxlength="4"
              placeholder="Confirm" class="input tracking-[0.5em] text-center" required />
          </div>
          <button class="btn btn-primary w-full" type="submit">Update PIN</button>
        </form>
        <div class="h-px bg-line"></div>
        <form id="deleteForm" class="space-y-3">
          <label class="text-xs font-medium text-muted uppercase tracking-wider">Danger zone</label>
          <p class="text-xs text-muted">Enter your PIN to permanently delete this account.</p>
          <div class="flex gap-2">
            <input name="pin" type="password" inputmode="numeric" maxlength="4"
              placeholder="PIN" class="input flex-1 tracking-[0.5em] text-center" required />
            <button class="btn btn-danger px-4" type="submit">Delete</button>
          </div>
        </form>
      </div>`,
      () => {
        $("#nameForm").addEventListener("submit", async (e) => {
          e.preventDefault();
          const newName = e.target.elements.name.value.trim();
          if (!newName) return toast("Name cannot be empty.", "error");
          try {
            await api("/api/update", {
              account_number: State.currentUser.account_number,
              pin: State.currentUser.pin,
              new_name: newName,
            });
            State.currentUser.name = newName;
            renderDashboard(false);
            toast("Name updated.", "success");
            closeModal();
          } catch (err) { toast(err.message, "error"); }
        });

        $("#pinForm").addEventListener("submit", async (e) => {
          e.preventDefault();
          const f = e.target.elements;
          if (f.new_pin.value !== f.confirm_pin.value) return toast("PINs do not match.", "error");
          if (!/^\d{4}$/.test(f.new_pin.value)) return toast("PIN must be 4 digits.", "error");
          try {
            await api("/api/update", {
              account_number: State.currentUser.account_number,
              pin: f.old_pin.value,
              new_pin: f.new_pin.value,
            });
            State.currentUser.pin = f.new_pin.value;
            toast("PIN updated.", "success");
            closeModal();
          } catch (err) { toast(err.message, "error"); }
        });

        $("#deleteForm").addEventListener("submit", async (e) => {
          e.preventDefault();
          const pin = e.target.elements.pin.value;
          if (!confirm("Permanently delete this account? This cannot be undone.")) return;
          try {
            await api("/api/delete", {
              account_number: State.currentUser.account_number,
              pin,
            });
            closeModal();
            toast("Account deleted.", "info");
            showAuth();
          } catch (err) { toast(err.message, "error"); }
        });
      }
    );
  };

  // ---------- Account created modal ----------
  const openAccountCreatedModal = (acct) => {
    openModal(
      "Account created 🎉",
      "Save your account number — you'll need it to log in.",
      `<div class="space-y-4">
        <div class="rounded-xl border border-emerald-brand/40 bg-emerald-brand/5 p-4">
          <p class="text-[11px] uppercase tracking-wider text-emerald-glow">Your account number</p>
          <div class="mt-2 flex items-center justify-between gap-3">
            <span class="font-mono text-2xl tracking-widest">${acct.account_number}</span>
            <button id="copyNew" class="btn btn-ghost text-xs py-1.5 px-3">Copy</button>
          </div>
        </div>
        <p class="text-xs text-muted">Welcome aboard, <span class="text-white">${acct.name}</span>. You'll be signed in automatically.</p>
        <button id="continueBtn" class="btn btn-primary w-full">Continue to dashboard</button>
      </div>`,
      () => {
        $("#copyNew").addEventListener("click", () => {
          navigator.clipboard?.writeText(acct.account_number);
          toast("Account number copied.", "success");
        });
        $("#continueBtn").addEventListener("click", () => {
          closeModal();
          showDashboard();
        });
      }
    );
  };

  // ---------- Auth ----------
  const wireAuth = () => {
    $$(".auth-tab").forEach(tab => {
      tab.addEventListener("click", () => {
        const which = tab.dataset.tab;
        $$(".auth-tab").forEach(t => {
          t.classList.toggle("tab-active", t === tab);
          t.classList.toggle("text-muted", t !== tab);
        });
        $("#loginForm").classList.toggle("hidden", which !== "login");
        $("#signupForm").classList.toggle("hidden", which !== "signup");
      });
    });

    $("#loginForm").addEventListener("submit", async (e) => {
      e.preventDefault();
      const f = e.target.elements;
      const num = f.account_number.value.trim().toUpperCase();
      const pin = f.pin.value.trim();
      if (num.length !== 10) return toast("Account number must be 10 characters.", "error");
      if (!/^\d{4}$/.test(pin)) return toast("PIN must be 4 digits.", "error");
      const btn = e.target.querySelector("[type=submit]");
      btn.disabled = true;
      try {
        const data = await api("/api/login", { account_number: num, pin });
        State.currentUser = { ...data, pin };
        toast(`Welcome back, ${data.name}!`, "success");
        showDashboard();
      } catch (err) {
        toast(err.message, "error");
      } finally {
        btn.disabled = false;
      }
    });

    $("#signupForm").addEventListener("submit", async (e) => {
      e.preventDefault();
      const f = e.target.elements;
      const name = f.name.value.trim();
      const pin = f.pin.value.trim();
      const conf = f.confirm_pin.value.trim();
      if (!name) return toast("Name is required.", "error");
      if (!/^\d{4}$/.test(pin)) return toast("PIN must be 4 digits.", "error");
      if (pin !== conf) return toast("PINs do not match.", "error");
      const btn = e.target.querySelector("[type=submit]");
      btn.disabled = true;
      try {
        const data = await api("/api/signup", { name, pin });
        State.currentUser = { ...data, pin };
        e.target.reset();
        openAccountCreatedModal(data);
      } catch (err) {
        toast(err.message, "error");
      } finally {
        btn.disabled = false;
      }
    });
  };

  // ---------- Wire app ----------
  const wireApp = () => {
    $("#navLogoutBtn").addEventListener("click", () => {
      toast("Signed out.", "info");
      showAuth();
    });

    $("#navAdminBtn").addEventListener("click", showAdmin);
    $("#adminBackBtn").addEventListener("click", () =>
      State.currentUser ? showDashboard() : showAuth()
    );

    $$("[data-action]").forEach(b =>
      b.addEventListener("click", () => {
        const a = b.dataset.action;
        if (a === "deposit") openAmountModal("deposit");
        if (a === "withdraw") openAmountModal("withdraw");
        if (a === "settings") openSettingsModal();
      })
    );

    $("#copyAcctBtn").addEventListener("click", () => {
      if (!State.currentUser) return;
      navigator.clipboard?.writeText(State.currentUser.account_number);
      toast("Account number copied.", "success");
    });

    $("#txSearch").addEventListener("input", renderTransactions);
    $("#adminSearch").addEventListener("input", renderAdmin);

    document.addEventListener("click", (e) => {
      if (e.target.matches("[data-close-modal]")) closeModal();
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeModal();
    });

    document.addEventListener("input", (e) => {
      const t = e.target;
      if (t.matches('input[name="account_number"]'))
        t.value = t.value.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 10);
      if (t.matches('input[name="pin"], input[name="confirm_pin"], input[name="old_pin"], input[name="new_pin"]'))
        if (t.type === "password") t.value = t.value.replace(/\D/g, "").slice(0, 4);
    });
  };

  // ---------- Boot ----------
  document.addEventListener("DOMContentLoaded", () => {
    wireAuth();
    wireApp();
    showAuth();
  });
})();