"use client";

import { useCallback, useEffect, useState } from "react";
import { CheckCircle2, ExternalLink, Plus, RefreshCw, ShieldCheck, Trash2 } from "lucide-react";
import { Button, Card, ErrorNote } from "./ui";
import { useI18n } from "@/i18n/client";
import { connectCall, MuseConnectDialog, type ConnectTarget } from "./muse-connect-dialog";
import { DeleteMuseAccountDialog } from "./delete-muse-account-dialog";

type Account = { id: string; label: string; enabled: boolean; ok: boolean | null };

export function AccountsPanel() {
  const { locale } = useI18n();
  const vi = locale === "vi";
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [target, setTarget] = useState<ConnectTarget | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Account | null>(null);
  const active = target !== null || deleteTarget !== null;
  const load = useCallback(async () => {
    try {
      const response = await fetch("/api/muse-connect", { cache: "no-store" });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error);
      setAccounts(data.accounts);
      setError("");
    } catch { setError("Không tải được tài khoản. Kiểm tra kết nối rồi tải lại trang."); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => {
    let stopped = false;
    const timer = setTimeout(() => {
      void load();
      void connectCall("resume").then(result => {
        if (!stopped && result.active) setTarget({ resume: true });
      }).catch(() => {});
    }, 0);
    return () => { stopped = true; clearTimeout(timer); };
  }, [load]);
  function start(account?: Account) {
    setError(""); setSuccess("");
    setTarget(account ? { id: account.id, label: account.label } : {});
  }
  return <>
    <Card className="mb-6 flex min-w-0 flex-col gap-4 p-4 sm:flex-row sm:items-center sm:justify-between sm:p-6">
      <div className="flex min-w-0 items-start gap-3">
        <span className="flex size-11 shrink-0 items-center justify-center rounded-2xl bg-accent-soft text-gold"><ShieldCheck className="size-5" /></span>
        <div className="min-w-0"><h2 className="font-semibold">{vi ? "Kết nối tài khoản" : "Connect an account"}</h2>
          <p className="mt-1 max-w-lg text-sm leading-relaxed text-muted">{vi ? "Đăng nhập Muse để tạo video. Không cần cài tiện ích." : "Sign in to Muse to create videos. No extension needed."}</p></div>
      </div>
      <Button disabled={active} onClick={() => void start()} className="min-h-11">
        <Plus />{vi ? "Kết nối Muse" : "Connect Muse"}
      </Button>
    </Card>
    <div className="mb-3 flex min-w-0 items-center justify-between gap-3"><h2 className="text-sm font-semibold">{vi ? "Tài khoản đã kết nối" : "Connected accounts"}<span className="ml-2 text-xs font-normal text-subtle">{loading ? "…" : accounts.length}</span></h2><span className="shrink-0 rounded-full bg-surface-soft px-2 py-1 text-[10px] text-subtle">{vi ? "Bản thử nghiệm" : "Preview"}</span></div>
    {success && <div role="status" className="mb-5 flex items-center gap-2 rounded-xl bg-success/10 p-4 text-sm text-success"><CheckCircle2 className="size-4" />{success}</div>}
    {error && !active && <div role="alert" className="mb-5"><ErrorNote>{error}</ErrorNote></div>}
    {loading ? <p className="text-sm text-muted">{vi ? "Đang tải tài khoản…" : "Loading accounts…"}</p> : accounts.length === 0 ?
      <Card className="p-8 text-center text-sm text-muted">{vi ? "Chưa có tài khoản. Kết nối Muse để bắt đầu." : "No accounts yet. Connect Muse to get started."}</Card> :
      <div className="grid gap-3 md:grid-cols-2">{accounts.map(account => <Card key={account.id} className="flex min-w-0 items-center justify-between gap-3 p-4">
        <div className="min-w-0 flex-1"><p className="truncate text-sm font-semibold" title={account.label}>{account.label}</p>
          <p className="mt-1 flex items-center gap-1.5 text-xs text-muted"><span className={`size-1.5 rounded-full ${!account.enabled ? "bg-subtle" : account.ok === false ? "bg-danger" : account.ok === true ? "bg-success" : "bg-warning"}`} />
            {!account.enabled ? (vi ? "Đã tắt" : "Disabled") : account.ok === false ? (vi ? "Cần kiểm tra" : "Needs attention") : account.ok === true ? (vi ? "Lần kiểm tra: hợp lệ" : "Last check: valid") : (vi ? "Chưa xác minh" : "Not verified")}</p></div>
        <div className="flex shrink-0 items-center gap-1">
          <Button variant="secondary" size="sm" disabled={active} aria-label={`${vi ? "Thay tài khoản" : "Replace account"}: ${account.label}`} onClick={() => void start(account)}><RefreshCw /><span className="sm:hidden">{vi ? "Thay" : "Replace"}</span><span className="hidden sm:inline">{vi ? "Thay tài khoản" : "Replace account"}</span></Button>
          <Button variant="ghost" size="icon" disabled={active} className="min-h-11 min-w-11 !text-subtle hover:!bg-danger/10 hover:!text-danger" title={vi ? "Xóa kết nối" : "Remove connection"} aria-label={`${vi ? "Xóa kết nối" : "Remove connection"}: ${account.label}`} onClick={() => { setError(""); setDeleteTarget(account); }}><Trash2 /></Button>
        </div>
      </Card>)}</div>}
    <details className="mt-6 text-xs text-muted"><summary>{vi ? "Cài đặt nâng cao" : "Advanced settings"}</summary>
      <p className="mt-3 leading-relaxed">{vi ? "Bản thử nghiệm trên máy chủ hiện tại. Phiên đăng nhập tự đóng sau 15 phút. Chỉ lưu phiên khi bạn bấm Hoàn tất và Muse xác minh thành công." : "Local-server prototype. Sign-in closes after 15 minutes. A session is saved only after you finish and Muse verifies it."}</p>
      <a href="http://localhost:18610/admin" target="_blank" rel="noopener noreferrer" className="mt-3 inline-flex items-center gap-2 text-gold">{vi ? "Mở quản trị Muse2API trên máy chủ này" : "Open Muse2API admin on this computer"}<ExternalLink className="size-3" /></a>
    </details>

    {target && <MuseConnectDialog target={target} onClose={() => setTarget(null)} onConnected={(name) => {
      setTarget(null);
      setSuccess(vi ? `Đã kết nối ${name}.` : `Connected ${name}.`);
      void load();
      window.dispatchEvent(new Event("muse-accounts-changed"));
    }} />}
    {deleteTarget && <DeleteMuseAccountDialog account={deleteTarget} onClose={() => setDeleteTarget(null)} onDeleted={() => {
      setAccounts(rows => rows.filter(row => row.id !== deleteTarget.id));
      setSuccess(vi ? `Đã gỡ kết nối ${deleteTarget.label}.` : `Removed ${deleteTarget.label}.`);
      setDeleteTarget(null);
      window.dispatchEvent(new Event("muse-accounts-changed"));
    }} />}
  </>;
}
