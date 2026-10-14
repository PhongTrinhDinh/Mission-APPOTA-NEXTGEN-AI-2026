"use client";

import React, { useState, useEffect, useRef } from "react";
import { ragApi, UserProfile, SourceNodeInfo, HealthResponse } from "@/lib/api";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  userName?: string;
  userId?: string;
  timestamp: string;
  sources?: SourceNodeInfo[];
  isError?: boolean;
}

export default function Home() {
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<string>("");
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuery, setInputQuery] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isIngesting, setIsIngesting] = useState<boolean>(false);

  const [isBackendOnline, setIsBackendOnline] = useState<boolean | null>(null);
  const [healthData, setHealthData] = useState<HealthResponse | null>(null);
  const [showHealthModal, setShowHealthModal] = useState<boolean>(false);
  const [collapsedSources, setCollapsedSources] = useState<Record<string, boolean>>({});

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Cuộn xuống tin nhắn mới nhất
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Khởi động: Kiểm tra backend và nạp người dùng (có cơ chế auto-retry khi backend đang khởi động)
  const checkBackendAndLoadUsers = async (isManual = false) => {
    try {
      const health = await ragApi.getHealth();
      setHealthData(health);
      setIsBackendOnline(health.is_ready);

      const userList = await ragApi.getUsers();
      setUsers(userList);
      if (userList.length > 0) {
        setSelectedUserId((prev) => prev || userList[0].user_id);
        setCurrentUser((prev) => prev || userList[0]);

        setMessages((prev) => {
          if (prev.length > 0) return prev;
          return [
            {
              id: "welcome-msg",
              role: "assistant",
              text: `Xin chào! Tôi là Trợ lý AI Tra Cứu Chính Sách của Appota Group.\n\nHệ thống được bảo vệ bằng Hard Filtering RBAC: Bạn chỉ có thể tra cứu thông tin tương thích với cấp bậc và phòng ban của tài khoản đang chọn bên trái.\n\nHãy chọn một nhân viên và thử đặt câu hỏi!`,
              timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
            },
          ];
        });
      }
      return true;
    } catch (err) {
      if (isManual) console.warn("Backend retry error:", err);
      setIsBackendOnline(false);
      return false;
    }
  };

  useEffect(() => {
    let retryCount = 0;
    let timerId: NodeJS.Timeout;

    const runInitWithRetry = async () => {
      const success = await checkBackendAndLoadUsers();
      if (!success && retryCount < 15) {
        retryCount += 1;
        timerId = setTimeout(runInitWithRetry, 2500);
      }
    };

    runInitWithRetry();

    return () => {
      if (timerId) clearTimeout(timerId);
    };
  }, []);

  // Xử lý đổi User
  const handleUserChange = (userId: string) => {
    setSelectedUserId(userId);
    const u = users.find((x) => x.user_id === userId) || null;
    setCurrentUser(u);
  };

  // Gửi câu hỏi Chat
  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const query = inputQuery.trim();
    if (!query || !currentUser || isLoading) return;

    const userMsgId = `user-${Date.now()}`;
    const newMsg: ChatMessage = {
      id: userMsgId,
      role: "user",
      text: query,
      userName: currentUser.name,
      userId: currentUser.user_id,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, newMsg]);
    setInputQuery("");
    setIsLoading(true);

    try {
      const resp = await ragApi.chat(currentUser.user_id, query);
      const aiMsg: ChatMessage = {
        id: `ai-${Date.now()}`,
        role: "assistant",
        text: resp.response,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        sources: resp.source_details || [],
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : "Đã xảy ra lỗi không xác định";
      const errorChatMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        role: "assistant",
        text: `⚠️ **Không thể truy vấn:** ${errorMsg}`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        isError: true,
      };
      setMessages((prev) => [...prev, errorChatMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  // Nút kịch bản kiểm thử (giữ nguyên User đang chọn để kiểm tra phân quyền RBAC độc lập)
  const handleQuickQuestion = (question: string) => {
    setInputQuery(question);
  };

  // Nút Re-ingest
  const handleReingest = async () => {
    if (!confirm("Bạn có chắc chắn muốn quét và lập lại chỉ mục toàn bộ tài liệu Markdown vào Qdrant?")) return;
    setIsIngesting(true);
    try {
      const res = await ragApi.ingest();
      alert(`✅ ${res.message}`);
    } catch (err: unknown) {
      alert(`❌ Lỗi Ingest: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setIsIngesting(false);
    }
  };

  // Mở modal cấu hình
  const handleOpenHealth = async () => {
    setShowHealthModal(true);
    try {
      const data = await ragApi.getHealth();
      setHealthData(data);
      setIsBackendOnline(data.is_ready);
    } catch {
      setIsBackendOnline(false);
    }
  };

  // Toggle danh sách nguồn
  const toggleSources = (msgId: string) => {
    setCollapsedSources((prev) => ({
      ...prev,
      [msgId]: !prev[msgId],
    }));
  };

  // Render markdown đơn giản (bold, bullets)
  const renderFormattedText = (rawText: string) => {
    const lines = rawText.split("\n");
    return lines.map((line, idx) => {
      // Bold replace
      const formatted = line.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
      return (
        <span
          key={idx}
          dangerouslySetInnerHTML={{ __html: formatted }}
          style={{ display: "block", minHeight: line.trim() === "" ? "8px" : undefined }}
        />
      );
    });
  };

  return (
    <>
      {/* Header Bar */}
      <header className="navbar">
        <div className="brand-group">
          <div className="brand-logo" id="brand-logo-icon">A</div>
          <div className="brand-title">
            <h1>Appota NextGen Enterprise Secure RAG</h1>
            <p>Next.js 16 Client • FastAPI Backend • Hybrid Search (Dense+BM25) • FlashRank</p>
          </div>
        </div>

        <div className="nav-actions">
          <span
            id="backend-status-badge"
            className={`badge-status ${isBackendOnline === false ? "offline" : ""}`}
            style={{ cursor: isBackendOnline === false ? "pointer" : "default" }}
            onClick={() => isBackendOnline === false && checkBackendAndLoadUsers(true)}
            title={isBackendOnline === false ? "Click để thử kết nối lại với Backend" : ""}
          >
            {isBackendOnline === true
              ? "FastAPI Online"
              : isBackendOnline === false
              ? "Đang kết nối... (Click thử lại)"
              : "Đang kiểm tra..."}
          </span>
          <button id="btn-open-health-modal" className="btn-nav" onClick={handleOpenHealth}>
            ⚙️ Cấu Hình
          </button>
          <a
            id="link-swagger-docs"
            href={process.env.NEXT_PUBLIC_SWAGGER_URL || "/docs"}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-nav"
          >
            📄 Swagger Docs
          </a>
        </div>
      </header>

      {/* Main Container */}
      <div className="app-layout">
        {/* Sidebar: Phân Quyền & Danh Tính RBAC */}
        <aside className="sidebar">
          <div>
            <div className="section-title">Danh Tính & Phân Quyền (RBAC)</div>
            <div className="user-selector-card">
              <label htmlFor="user-select-dropdown" style={{ fontSize: "12px", color: "var(--text-muted)", fontWeight: 600 }}>
                Chọn Nhân Viên Đăng Nhập:
              </label>
              <select
                id="user-select-dropdown"
                className="user-select"
                value={selectedUserId}
                onChange={(e) => handleUserChange(e.target.value)}
              >
                {users.map((u) => (
                  <option key={u.user_id} value={u.user_id}>
                    [{u.user_id}] {u.name} - {u.dept} (L{u.role_level})
                  </option>
                ))}
              </select>

              {currentUser && (
                <div className="profile-preview">
                  <div className="profile-row">
                    <span className="profile-label">Họ và tên:</span>
                    <span className="profile-val" id="profile-user-name">{currentUser.name}</span>
                  </div>
                  <div className="profile-row">
                    <span className="profile-label">Phòng ban:</span>
                    <span className="profile-val" id="profile-user-dept">{currentUser.dept}</span>
                  </div>
                  <div className="profile-row">
                    <span className="profile-label">Cấp bậc:</span>
                    <span className={`badge-level level-${currentUser.role_level}`} id="profile-user-level">
                      Level {currentUser.role_level}
                    </span>
                  </div>
                  <div className="profile-row">
                    <span className="profile-label">Công ty:</span>
                    <span className="profile-val">{currentUser.company}</span>
                  </div>
                </div>
              )}

              <div className="rbac-scope-box" id="rbac-permission-explanation">
                {currentUser && currentUser.role_level >= 4 ? (
                  <span>
                    🌟 <b>C-Level/BOD:</b> Được phép tra cứu toàn bộ tài liệu từ Cấp 1 đến Level {currentUser.role_level} trên <b>toàn bộ phòng ban</b>.
                  </span>
                ) : currentUser ? (
                  <span>
                    🔒 <b>Phạm vi:</b> Chỉ đọc tài liệu Cấp ≤ <b>{currentUser.role_level}</b> và thuộc phòng <b>{currentUser.dept}</b> hoặc <b>ALL</b>.
                  </span>
                ) : null}
              </div>
            </div>
          </div>

          <div>
            <div className="section-title">5 Kịch Bản Kiểm Thử Độc Lập Với Tài Khoản</div>
            <p style={{ fontSize: "11px", color: "var(--text-faint)", marginBottom: "10px", lineHeight: 1.4 }}>
              💡 Chọn bất kỳ tài khoản nào bên trên, sau đó bấm kịch bản để quan sát cơ chế phân quyền (RBAC) và năng lực xử lý dữ liệu của AI:
            </p>
            <div className="quick-queries-list">
              {/* Kịch bản 1: Phân quyền phòng ban - Hoa hồng Sales */}
              <button
                id="scenario-1-btn"
                className="btn-quick-query"
                onClick={() =>
                  handleQuickQuestion(
                    "Chính sách hoa hồng bán hàng và cơ chế tính thưởng doanh số của khối Kinh doanh (Sales) được quy định như thế nào?"
                  )
                }
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", width: "100%" }}>
                  <span className="badge-query-tag tag-scenario-success">KB 1 • Nghiệp vụ Sales</span>
                  <span style={{ fontSize: "10px", fontWeight: 600, color: currentUser && (currentUser.dept === "Sales" || currentUser.role_level >= 4) ? "#34d399" : "#f87171" }}>
                    {currentUser && (currentUser.dept === "Sales" || currentUser.role_level >= 4) ? "Có quyền xem ✅" : "Bị chặn RBAC 🔒"}
                  </span>
                </div>
                <span style={{ fontWeight: 600 }}>Chính sách hoa hồng & thưởng KPI Sales</span>
                <span style={{ fontSize: "11px", color: "var(--text-faint)" }}>
                  Phạm vi: Phòng Sales hoặc BOD (C-Level)
                </span>
              </button>

              {/* Kịch bản 2: Bảo mật cấp bậc tuyệt mật C-Level */}
              <button
                id="scenario-2-btn"
                className="btn-quick-query"
                onClick={() =>
                  handleQuickQuestion(
                    "Quy định về khung thang bảng lương cấp quản lý cấp cao (C-Level/Director) và quy trình xử lý kỷ luật sa thải đặc biệt?"
                  )
                }
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", width: "100%" }}>
                  <span className="badge-query-tag tag-scenario-success">KB 2 • Bảo mật C-Level</span>
                  <span style={{ fontSize: "10px", fontWeight: 600, color: currentUser && currentUser.role_level >= 4 ? "#34d399" : "#f87171" }}>
                    {currentUser && currentUser.role_level >= 4 ? "Có quyền xem ✅" : "Bị chặn RBAC 🔒"}
                  </span>
                </div>
                <span style={{ fontWeight: 600 }}>Bảng lương mật C-Level & Sa thải đặc biệt</span>
                <span style={{ fontSize: "11px", color: "var(--text-faint)" }}>
                  Yêu cầu: Level ≥ 4 (BOD/C-Level). Cấp 1-3 bị chặn tuyệt đối.
                </span>
              </button>

              {/* Kịch bản 3: Tình huống khó - Đa phiên bản & Xung đột thời gian */}
              <button
                id="scenario-3-btn"
                className="btn-quick-query"
                onClick={() =>
                  handleQuickQuestion(
                    "Theo quy định hiện hành của công ty, số ngày nghỉ phép năm tối đa được phép chuyển sang năm sau là bao nhiêu ngày và hạn chót sử dụng là khi nào?"
                  )
                }
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", width: "100%" }}>
                  <span className="badge-query-tag tag-scenario-warning">KB 3 • Khó (Đa phiên bản)</span>
                  <span style={{ fontSize: "10px", fontWeight: 600, color: "#34d399" }}>
                    Tất cả NV xem được ✅
                  </span>
                </div>
                <span style={{ fontWeight: 600 }}>Xung đột chuyển ngày phép (2022 vs 2025)</span>
                <span style={{ fontSize: "11px", color: "var(--text-faint)" }}>
                  Thử thách: Hybrid Search & FlashRank phân biệt bản cũ vs bản mới
                </span>
              </button>

              {/* Kịch bản 4: Tình huống khó - Tổng hợp đa nguồn */}
              <button
                id="scenario-4-btn"
                className="btn-quick-query"
                onClick={() =>
                  handleQuickQuestion(
                    "Quy định về chế độ làm việc từ xa (Remote/Hybrid) và định mức hỗ trợ trang thiết bị làm việc tại nhà được áp dụng như thế nào?"
                  )
                }
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", width: "100%" }}>
                  <span className="badge-query-tag tag-scenario-warning">KB 4 • Khó (Tổng hợp kép)</span>
                  <span style={{ fontSize: "10px", fontWeight: 600, color: "#34d399" }}>
                    Tất cả NV xem được ✅
                  </span>
                </div>
                <span style={{ fontWeight: 600 }}>Tổng hợp: Chế độ Remote + Trợ cấp thiết bị</span>
                <span style={{ fontSize: "11px", color: "var(--text-faint)" }}>
                  Thử thách: Kéo đồng thời 2 tài liệu POL-HR-003 & POL-HR-REM-001
                </span>
              </button>

              {/* Kịch bản 5: Chưa tốt / Thất bại - Ngoài phạm vi tài liệu RAG */}
              <button
                id="scenario-5-btn"
                className="btn-quick-query"
                onClick={() =>
                  handleQuickQuestion(
                    "Tính đến hôm nay, cá nhân tôi còn lại chính xác bao nhiêu ngày nghỉ phép chưa sử dụng trong năm nay và đã nộp đơn nghỉ vào những ngày nào?"
                  )
                }
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", width: "100%" }}>
                  <span className="badge-query-tag tag-scenario-danger">KB 5 • Giới hạn thất bại</span>
                  <span style={{ fontSize: "10px", fontWeight: 600, color: "#f87171" }}>
                    Ngoài CSDL RAG ⚠️
                  </span>
                </div>
                <span style={{ fontWeight: 600 }}>Hỏi số dư phép cá nhân thực tế (Real-time)</span>
                <span style={{ fontSize: "11px", color: "var(--text-faint)" }}>
                  Thử thách: Nhận diện thiếu CSDL chấm công ERP, không bịa đặt
                </span>
              </button>
            </div>
          </div>

          <div style={{ marginTop: "auto", paddingTop: "12px" }}>
            <button
              id="btn-trigger-reingest"
              className="btn-nav"
              style={{ width: "100%", justifyContent: "center", padding: "10px" }}
              onClick={handleReingest}
              disabled={isIngesting}
            >
              {isIngesting ? "⏳ Đang quét Qdrant..." : "🔄 Tái Quét Chỉ Mục (Ingest)"}
            </button>
          </div>
        </aside>

        {/* Main Chat Workspace */}
        <main className="chat-workspace">
          <div className="chat-messages" id="chat-messages-container">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`message-bubble ${msg.role === "user" ? "user" : "assistant"}`}
                id={`message-bubble-${msg.id}`}
              >
                <div className={`avatar ${msg.role === "user" ? "user-avatar" : "ai-avatar"}`}>
                  {msg.role === "user" ? (msg.userName ? msg.userName.charAt(0) : "U") : "AI"}
                </div>
                <div className="message-content">
                  <div className="message-sender">
                    <span>{msg.role === "user" ? `${msg.userName} (${msg.userId})` : "Appota Secure Assistant"}</span>
                    <span>•</span>
                    <span style={{ color: msg.role === "user" ? "#93c5fd" : msg.isError ? "#ef4444" : "#10b981" }}>
                      {msg.role === "user" ? "User Query" : msg.isError ? "Error" : "RBAC Filtered"}
                    </span>
                    <span style={{ marginLeft: "auto", fontSize: "10px", color: "var(--text-faint)" }}>
                      {msg.timestamp}
                    </span>
                  </div>

                  <div className="message-body">{renderFormattedText(msg.text)}</div>

                  {msg.sources && msg.sources.length > 0 && (
                    <div className="message-sources">
                      <div
                        className="sources-header"
                        onClick={() => toggleSources(msg.id)}
                        role="button"
                        tabIndex={0}
                      >
                        <span>📑 Trích dẫn {msg.sources.length} tài liệu liên quan</span>
                        <span style={{ fontSize: "10px", marginLeft: "4px" }}>
                          {collapsedSources[msg.id] ? "▼" : "▲"}
                        </span>
                      </div>

                      {!collapsedSources[msg.id] && (
                        <div className="sources-list">
                          {msg.sources.map((s, idx) => (
                            <div key={idx} className="source-item">
                              <div className="source-top-line">
                                <span>📄 {s.title || "Tài liệu"}</span>
                                {s.score !== undefined && s.score !== null && (
                                  <span className="source-score">Rerank: {s.score}</span>
                                )}
                              </div>
                              <div style={{ fontSize: "10px", color: "#64748b" }}>
                                Cấp độ: L{s.required_level || 1} • Phòng ban: {s.required_dept || "ALL"}
                              </div>
                              {s.text_excerpt && (
                                <div className="source-excerpt">
                                  &quot;{s.text_excerpt}...&quot;
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="message-bubble assistant" id="chat-loading-indicator">
                <div className="avatar ai-avatar">AI</div>
                <div className="message-content">
                  <div className="message-sender">
                    <span>Appota Secure Assistant</span>
                    <span>•</span>
                    <span style={{ color: "var(--primary)" }}>Đang tra cứu Hybrid & Rerank...</span>
                  </div>
                  <div className="loading-indicator">
                    <span className="dot"></span>
                    <span className="dot"></span>
                    <span className="dot"></span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Chat Input Container */}
          <div className="chat-input-container">
            <form id="chat-form-element" className="input-form" onSubmit={handleSendMessage}>
              <input
                id="chat-input-field"
                type="text"
                className="chat-input"
                placeholder={
                  currentUser
                    ? `Đặt câu hỏi chính sách dưới danh nghĩa ${currentUser.name} (${currentUser.dept} - L${currentUser.role_level})...`
                    : "Nhập câu hỏi tra cứu chính sách..."
                }
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                disabled={isLoading}
                autoComplete="off"
              />
              <button
                id="send-message-btn"
                type="submit"
                className="btn-send"
                disabled={isLoading || !inputQuery.trim()}
              >
                <span>Gửi</span>
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13"></line>
                  <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                </svg>
              </button>
            </form>
          </div>
        </main>
      </div>

      {/* Health Check Modal */}
      {showHealthModal && (
        <div
          id="health-modal-overlay"
          className="modal-overlay"
          onClick={() => setShowHealthModal(false)}
        >
          <div className="modal-box" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 style={{ fontSize: "16px", fontWeight: 700, color: "#fff" }}>
                Thông Số Hệ Thống & Cấu Hình RAG
              </h2>
              <button
                id="btn-close-health-modal"
                className="modal-close"
                onClick={() => setShowHealthModal(false)}
              >
                &times;
              </button>
            </div>
            <p style={{ fontSize: "13px", color: "var(--text-muted)" }}>
              Dữ liệu lấy từ endpoint <code style={{ color: "var(--primary)" }}>GET /api/health</code>
            </p>

            <div className="health-grid">
              <div className="health-card">
                <div className="title">Trạng thái Service</div>
                <div className="value" style={{ color: isBackendOnline ? "#34d399" : "#f87171" }}>
                  {isBackendOnline ? "READY (200 OK)" : "DISCONNECTED"}
                </div>
              </div>
              <div className="health-card">
                <div className="title">Hybrid Search</div>
                <div className="value">
                  {healthData?.config.enable_hybrid ? "Bật (Dense + BM25)" : "Tắt"}
                </div>
              </div>
              <div className="health-card">
                <div className="title">Reranker Model</div>
                <div className="value">{healthData?.config.rerank_model || "-"}</div>
              </div>
              <div className="health-card">
                <div className="title">Sparse Model (BM25)</div>
                <div className="value">{healthData?.config.sparse_model || "-"}</div>
              </div>
              <div className="health-card">
                <div className="title">LLM Model</div>
                <div className="value">{healthData?.config.llm_model || "-"}</div>
              </div>
              <div className="health-card">
                <div className="title">Embedding Model</div>
                <div className="value">{healthData?.config.embedding_model || "-"}</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
