// ============================================================
//  思政教学程序 - 课内知识域
// ============================================================

// ─── 教材 ───
function renderTextbookItem(d) {
 const attrs = d.has_content ? ` data-open-textbook="1" data-book-id="${esc(d.id)}" data-book-title="${esc(d.name)}"` : "";
 return `<div class="data-item${d.has_content ? ' clickable' : ''}"${attrs}><div class="data-item-header">
   <div><div class="data-item-title">${esc(d.name)}</div>
   <div class="data-item-meta"><span>${esc(d.author)}</span><span>${esc(d.publisher)}</span><span>${esc(d.year)}</span></div></div>
   <div class="data-item-actions">
     ${d.has_content ? `<span class="badge badge-read">已导入</span>` : ""}
     <button class="btn btn-danger btn-sm" onclick="event.stopPropagation();deleteItem('/api/textbooks','${d.id}','textbook-list',renderTextbookItem)">删除</button>
   </div></div>
   ${d.description ? `<div class="data-item-body">${esc(d.description)}</div>` : ""}
 </div>`;
}

function showTextbookForm() { showForm("textbook-form"); }

async function saveTextbook() {
 const item = { name: g("tb-name"), author: g("tb-author"), publisher: g("tb-publisher"), year: g("tb-year"), isbn: g("tb-isbn"), description: g("tb-desc") };
 await api("/api/textbooks", "POST", item);
 closeForm("textbook-form");
 fetchData("/api/textbooks", "textbook-list", renderTextbookItem);
}

var currentBookContent = null;
var currentReaderModel = null;
var currentReaderState = { chapterIdx: 0, sectionIdx: -1 };
var currentBookTitle = "";
var readerTocCollapsed = false;
var readerTocExpandedChapters = {};

function cleanReaderHeading(text) {
  return String(text || "")
    .replace(/\s+/g, " ")
    .replace(/[\/／]\s*\d+\s*$/, "")
    .replace(/\s+\d{1,3}\s*$/, "")
    .trim();
}

function compactReaderText(text) {
  return cleanReaderHeading(text).replace(/\s+/g, "");
}

function isReaderMainChapterTitle(text) {
  var compact = compactReaderText(text);
  if (/^\u7eea\u8bba/.test(compact)) return true;
  var match = compact.match(/^\u7b2c[\u4e00\u4e8c\u4e09\u56db\u4e94\u516d\u4e03\u516b\u4e5d\u5341\u767e0-9]+\u7ae0(.+)$/);
  if (!match) return false;
  return match[1].replace(/[\/\d\s]+$/g, "").length >= 2;
}

function isReaderSectionTitle(text) {
  return /^\u7b2c[\u4e00\u4e8c\u4e09\u56db\u4e94\u516d\u4e03\u516b\u4e5d\u5341\u767e0-9]+\u8282/.test(compactReaderText(text));
}

function getReaderSectionOrdinal(text) {
  var match = compactReaderText(text).match(/^\u7b2c([\u4e00\u4e8c\u4e09\u56db\u4e94\u516d\u4e03\u516b\u4e5d\u5341\u767e0-9]+)\u8282/);
  return match ? match[1] : "";
}

function isReaderSubheading(text) {
  var compact = compactReaderText(text);
  return /^[一二三四五六七八九十百0-9]+[、.．]/.test(compact)
    || /^[（(][一二三四五六七八九十百0-9]+[)）]/.test(compact);
}

function isReaderReferenceLike(text) {
  var compact = compactReaderText(text);
  return compact === "思考讨论"
    || compact === "文献阅读"
    || /^\d+[.、]/.test(compact)
    || /^(本书编写组|主要成员|马克思主义理论研究和建设工程|目录|后记)/.test(compact);
}

function cleanReaderParagraph(text) {
  var cleaned = String(text || "").replace(/\s+/g, " ").trim();
  var compact = cleaned.replace(/\s+/g, "");
  if (!compact) return "";
  if (/^[ivxlcdm]+目录$/i.test(compact) || /^目录$/.test(compact)) return "";
  if (/^\d{1,3}$/.test(compact)) return "";
  if (/^\d{1,3}(绪论|第[一二三四五六七八九十百0-9]+章)/.test(compact)) return "";
  return cleaned;
}

function createReaderModel(rawContent) {
  var model = { id: rawContent?.id || "", title: rawContent?.title || "", chapters: [] };
  var currentChapter = null;
  var currentSection = null;
  var started = false;

  function ensureChapter(title) {
    var cleanTitle = cleanReaderHeading(title) || ("第" + (model.chapters.length + 1) + "章");
    var last = model.chapters[model.chapters.length - 1];
    if (last && compactReaderText(last.heading) === compactReaderText(cleanTitle)) {
      currentChapter = last;
      currentSection = last.sections[last.sections.length - 1] || null;
      return currentChapter;
    }
    currentChapter = {
      heading: cleanTitle,
      level: 1,
      sections: [],
      chapterNo: model.chapters.length + 1,
    };
    model.chapters.push(currentChapter);
    currentSection = null;
    started = true;
    return currentChapter;
  }

  function ensureSection(title, showInToc) {
    if (!currentChapter) return null;
    var cleanTitle = cleanReaderHeading(title);
    if (!cleanTitle) cleanTitle = currentChapter.sections.length ? "延伸阅读" : "导读";
    var key = compactReaderText(cleanTitle);
    var sectionNo = showInToc ? getReaderSectionOrdinal(cleanTitle) : "";
    var last = currentChapter.sections[currentChapter.sections.length - 1];
    if (last && (last.key === key || (!showInToc && !last.showInToc && last.heading === cleanTitle) || (showInToc && last.showInToc && sectionNo && last.sectionNo === sectionNo))) {
      currentSection = last;
      return currentSection;
    }
    currentSection = {
      heading: cleanTitle,
      level: showInToc ? 2 : 3,
      showInToc: !!showInToc,
      sectionNo,
      key,
      content: [],
    };
    currentChapter.sections.push(currentSection);
    return currentSection;
  }

  function addContentItems(items) {
    if (!currentChapter || !Array.isArray(items)) return;
    if (!currentSection) ensureSection("", false);
    items.forEach(function(item) {
      var cleaned = cleanReaderParagraph(item && item.text);
      if (!cleaned || !currentSection) return;
      currentSection.content.push({
        text: cleaned,
        style: item.style || "Normal",
        bold: !!item.bold,
        italic: !!item.italic,
      });
    });
  }

  function addInlineHeading(title) {
    if (!currentChapter) return;
    var cleanTitle = cleanReaderHeading(title);
    if (!cleanTitle || isReaderReferenceLike(cleanTitle)) return;
    if (!currentSection) ensureSection("", false);
    currentSection.content.push({ text: cleanTitle, kind: "subheading" });
  }

  (rawContent?.chapters || []).forEach(function(ch) {
    var chapterHeading = cleanReaderHeading(ch.heading);
    if (isReaderMainChapterTitle(chapterHeading)) {
      ensureChapter(chapterHeading);
    } else if (!started) {
      // Skip cover, editorial board and table-of-contents fragments before the real textbook body.
      currentChapter = null;
      currentSection = null;
    } else if (isReaderSectionTitle(chapterHeading)) {
      ensureSection(chapterHeading, true);
    } else if (isReaderSubheading(chapterHeading)) {
      addInlineHeading(chapterHeading);
    }

    (ch.sections || []).forEach(function(sec) {
      var sectionHeading = cleanReaderHeading(sec.heading);
      if (isReaderMainChapterTitle(sectionHeading)) {
        ensureChapter(sectionHeading);
        addContentItems(sec.content);
        return;
      }
      if (!started) return;
      if (isReaderSectionTitle(sectionHeading)) {
        ensureSection(sectionHeading, true);
      } else if (isReaderSubheading(sectionHeading) || (sectionHeading && !isReaderReferenceLike(sectionHeading))) {
        addInlineHeading(sectionHeading);
      }
      addContentItems(sec.content);
    });
  });

  model.chapters = model.chapters
    .map(function(ch) {
      ch.sections = ch.sections
        .filter(function(sec) { return sec.content && sec.content.length; })
        .map(function(sec, idx) {
          sec.index = idx;
          return sec;
        });
      return ch;
    })
    .filter(function(ch) { return ch.sections.length; });

  if (!model.chapters.length && rawContent && rawContent.chapters) {
    model.chapters = rawContent.chapters;
  }
  return model;
}

function setReaderText(id, text) {
  var el = document.getElementById(id);
  if (el) el.textContent = text;
}

function getReaderChapterTitle(chapter, chapterIdx) {
  if (!chapter) return "第" + (chapterIdx + 1) + "章";
  var title = (chapter.heading || "").trim();
  return title || ("第" + (chapterIdx + 1) + "章");
}

function setReaderTocExpanded(chapterIdx, expanded) {
  readerTocExpandedChapters[String(chapterIdx)] = expanded;
}

function isReaderTocExpanded(chapterIdx) {
  var key = String(chapterIdx);
  if (Object.prototype.hasOwnProperty.call(readerTocExpandedChapters, key)) {
    return !!readerTocExpandedChapters[key];
  }
  return currentReaderState.chapterIdx === chapterIdx;
}

function ensureReaderChapterVisible(chapterIdx) {
  if (chapterIdx >= 0) setReaderTocExpanded(chapterIdx, true);
}

function syncReaderTocLayout() {
  var container = document.getElementById("reader-container");
  var btn = document.getElementById("reader-toc-toggle");
  if (container) container.classList.toggle("toc-collapsed", readerTocCollapsed);
  if (btn) {
    btn.textContent = readerTocCollapsed ? "显示目录" : "收起目录";
    btn.setAttribute("aria-expanded", readerTocCollapsed ? "false" : "true");
  }
}

function toggleReaderToc(forceState) {
  if (typeof forceState === "boolean") readerTocCollapsed = forceState;
  else readerTocCollapsed = !readerTocCollapsed;
  syncReaderTocLayout();
}

function toggleReaderChapterGroup(chapterIdx, event) {
  if (event) {
    event.preventDefault();
    event.stopPropagation();
  }
  setReaderTocExpanded(chapterIdx, !isReaderTocExpanded(chapterIdx));
  renderReaderToc();
}

function scrollActiveReaderTocIntoView() {
  var activeItem = document.querySelector("#toc-list .toc-item.active a, #toc-list .toc-group-link.active");
  if (activeItem && typeof activeItem.scrollIntoView === "function") {
    activeItem.scrollIntoView({ block: "nearest" });
  }
}

function renderReaderToc() {
  var tocList = document.getElementById("toc-list");
  if (!tocList) return;
  tocList.innerHTML = "";

  var content = currentReaderModel || currentBookContent;
  if (!content || !content.chapters) return;

  content.chapters.forEach(function(ch, ci) {
    var group = document.createElement("li");
    var sections = Array.isArray(ch.sections) ? ch.sections.filter(function(sec) {
      return !!(sec && sec.showInToc && sec.heading && (sec.content && sec.content.length));
    }) : [];
    var expanded = isReaderTocExpanded(ci);
    var chapterTitle = getReaderChapterTitle(ch, ci);
    var chapterActive = currentReaderState.chapterIdx === ci && currentReaderState.sectionIdx === -1;

    group.className = "toc-group" + (expanded ? " expanded" : "") + (currentReaderState.chapterIdx === ci ? " current-chapter" : "");
    group.dataset.chapter = String(ci);

    var row = document.createElement("div");
    row.className = "toc-group-row";

    var toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "toc-group-toggle";
    toggle.textContent = expanded ? "-" : "+";
    toggle.title = expanded ? "收起本章目录" : "展开本章目录";
    toggle.onclick = function(event) { toggleReaderChapterGroup(ci, event); };
    row.appendChild(toggle);

    var chapterBtn = document.createElement("button");
    chapterBtn.type = "button";
    chapterBtn.className = "toc-group-link" + (chapterActive ? " active" : "");
    chapterBtn.textContent = chapterTitle;
    chapterBtn.onclick = function() {
      ensureReaderChapterVisible(ci);
      renderChapter(ci, -1);
    };
    row.appendChild(chapterBtn);

    if (sections.length) {
      var meta = document.createElement("span");
      meta.className = "toc-group-meta";
      meta.textContent = sections.length + "节";
      row.appendChild(meta);
    }

    group.appendChild(row);

    if (sections.length) {
      var subList = document.createElement("ul");
      subList.className = "toc-section-list";
      subList.hidden = !expanded;

      sections.forEach(function(sec) {
        var sectionIndex = typeof sec.index === "number" ? sec.index : ch.sections.indexOf(sec);
        var item = document.createElement("li");
        var sectionActive = currentReaderState.chapterIdx === ci && currentReaderState.sectionIdx === sectionIndex;
        item.className = "toc-item toc-l" + (sec.level || 2) + (sectionActive ? " active" : "");
        item.dataset.chapter = String(ci);
        item.dataset.section = String(sectionIndex);

        var link = document.createElement("a");
        link.href = "javascript:void(0)";
        link.textContent = (sec.heading || ("第" + (sectionIndex + 1) + "节")).trim();
        link.onclick = function() {
          ensureReaderChapterVisible(ci);
          renderChapter(ci, sectionIndex);
        };

        item.appendChild(link);
        subList.appendChild(item);
      });

      group.appendChild(subList);
    }

    tocList.appendChild(group);
  });

  scrollActiveReaderTocIntoView();
}

async function openTextbook(bookId, bookTitle) {
  try {
    var resp = await fetch("/api/textbooks/" + bookId + "/content", { headers: authHeaders() });
    if (!resp.ok) { alert("无法加载教材内容"); return; }
    currentBookContent = await resp.json();
    currentReaderModel = createReaderModel(currentBookContent);
    currentReaderState = { chapterIdx: 0, sectionIdx: -1 };
    currentBookTitle = bookTitle || currentReaderModel.title || currentBookContent.title || "教材阅读";
    navigateTo("textbook-reader");
    renderTextbookContent(currentBookTitle);
  } catch(err) {
    alert("加载失败: " + err.message);
  }
}

// ---- Smart Import ----
function resetSmartImportPanel() {
  setSmartImportCounts({ references: 0, syllabus: 0, textbook: 0, courseware: 0 });
  var result = document.getElementById("smart-import-result");
  if (result && !result.dataset.locked) {
    result.textContent = "请选择一个 Word 或 PDF 文件后开始导入。";
    result.className = "si-result";
  }
}

function setSmartImportCounts(summary) {
  var refs = document.getElementById("si-cnt-references");
  var syllabus = document.getElementById("si-cnt-syllabus");
  var textbook = document.getElementById("si-cnt-textbook");
  var courseware = document.getElementById("si-cnt-courseware");
  if (refs) refs.textContent = summary.references || 0;
  if (syllabus) syllabus.textContent = summary.syllabus || 0;
  if (textbook) textbook.textContent = summary.textbook || 0;
  if (courseware) courseware.textContent = summary.courseware || 0;
}

function setSmartImportBusy(isBusy) {
  var btn = document.getElementById("smart-import-btn");
  var loading = document.getElementById("smart-import-loading");
  if (btn) {
    btn.disabled = isBusy;
    btn.textContent = isBusy ? "正在导入..." : "开始导入";
  }
  if (loading) {
    loading.classList.toggle("hidden", !isBusy);
  }
}

async function smartImportDocument() {
  var input = document.getElementById("smart-import-file");
  var resultBox = document.getElementById("smart-import-result");
  if (!input || !input.files || !input.files[0]) {
    if (resultBox) {
      resultBox.textContent = "请先选择一个 Word 或 PDF 文件。";
      resultBox.className = "si-result si-error";
      resultBox.dataset.locked = "1";
    }
    return;
  }

  var file = input.files[0];
  var lowerName = file.name.toLowerCase();
  if (!lowerName.endsWith(".docx") && !lowerName.endsWith(".pdf")) {
    if (resultBox) {
      resultBox.textContent = "当前仅支持导入 .docx 和 .pdf 文件。";
      resultBox.className = "si-result si-error";
      resultBox.dataset.locked = "1";
    }
    return;
  }

  var reader = new FileReader();
  reader.onload = async function(ev) {
    var b64 = ev.target.result.split(",")[1];
    setSmartImportBusy(true);
    if (resultBox) {
      resultBox.textContent = "正在识别并分类内容...";
      resultBox.className = "si-result";
      resultBox.dataset.locked = "1";
    }
    try {
      var resp = await fetch("/api/smart-import", {
        method: "POST",
        headers: authHeaders({"Content-Type": "application/json"}),
        body: JSON.stringify({ filename: file.name, content: b64 })
      });
      var result = await resp.json();
      if (!resp.ok || !result.ok) {
        throw new Error(result.error || result.detail || "未知错误");
      }

      var s = result.summary || {};
      setSmartImportCounts(s);
      if (resultBox) {
        var readTitle = result.title || file.name;
        resultBox.innerHTML = "导入完成：" + esc(file.name) + "。内容已自动分配，可以在教材中打开阅读。" +
          (result.book_id ? ' <button class="btn btn-sm btn-primary" data-open-textbook="1" data-book-id="' + esc(result.book_id) + '" data-book-title="' + esc(readTitle) + '">立即阅读</button>' : "");
        resultBox.className = "si-result si-success";
      }
      fetchData("/api/textbooks", "textbook-list", renderTextbookItem);
      fetchData("/api/courseware", "courseware-list", renderCoursewareItem);
      fetchData("/api/syllabus", "syllabus-list", renderSyllabusItem);
      fetchData("/api/references", "reference-list", renderReferenceItem);
      input.value = "";
      if (typeof showSuccess === "function") showSuccess("智能导入完成");
    } catch (err) {
      if (resultBox) {
        resultBox.textContent = "导入失败：" + err.message;
        resultBox.className = "si-result si-error";
      }
      if (typeof showError === "function") showError("导入失败：" + err.message);
    } finally {
      setSmartImportBusy(false);
    }
  };
  reader.readAsDataURL(file);
}

function renderTextbookContent(bookTitle) {
  currentBookTitle = bookTitle || currentBookTitle || "教材阅读";
  setReaderText("reader-title", currentBookTitle);
  setReaderText("reader-book-title", currentBookTitle);
  setReaderText("reader-kicker", "电子教材");
  readerTocCollapsed = false;
  readerTocExpandedChapters = {};
  syncReaderTocLayout();
  var rc = document.getElementById("reader-content");
  if (rc) rc.className = "reader-content";
  var content = currentBookContent;
  var model = currentReaderModel || content;
  if (!model || !model.chapters) return;
  var chapterCount = model.chapters.length || 0;
  var sectionCount = model.chapters.reduce(function(total, ch) {
    return total + (ch.sections || []).filter(function(sec) { return sec.showInToc; }).length;
  }, 0);
  setReaderText("reader-meta-structure", chapterCount + " 章 · " + sectionCount + " 节");
  setReaderText("reader-book-subtitle", chapterCount ? "已优化目录结构，可按章节目阅读" : "当前教材暂无可展示章节");
  setReaderText("reader-progress", chapterCount ? "第 1 章" : "未开始");
  if (model.chapters.length > 0) renderChapter(0, -1);
  else renderReaderToc();
}

function renderChapter(chapterIdx, sectionIdx) {
  var container = document.getElementById("reader-content");
  var model = currentReaderModel || currentBookContent;
  if (!container || !model || !model.chapters) return;
  var ch = model.chapters[chapterIdx];
  if (!ch) return;
  currentReaderState = { chapterIdx: chapterIdx, sectionIdx: sectionIdx };
  var html = "";
  var chapterTitle = getReaderChapterTitle(ch, chapterIdx);
  var allSections = ch.sections || [];
  var visibleSections = allSections;
  var sectionTitle = "";
  if (sectionIdx >= 0) {
    visibleSections = [allSections[sectionIdx]];
    sectionTitle = allSections[sectionIdx] ? (allSections[sectionIdx].heading || "") : "";
  }

  setReaderText("reader-book-title", currentBookTitle || "教材阅读");
  setReaderText("reader-book-subtitle", sectionTitle || chapterTitle);
  setReaderText("reader-progress", "第 " + (chapterIdx + 1) + " 章");
  ensureReaderChapterVisible(chapterIdx);
  renderReaderToc();

  html += '<div class="reader-book-shell">';
  html += '<div class="reader-book-head">';
  html += '<div class="reader-book-meta"><span class="reader-meta-pill">教材</span><span class="reader-meta-pill">第 ' + (chapterIdx + 1) + " 章</span></div>";
  html += '<h2 class="reader-chapter-title">' + esc(chapterTitle) + "</h2>";
  html += '<div class="reader-book-subtitle">' + esc(sectionTitle || "按电子书样式整理后的阅读内容") + "</div>";
  html += "</div>";
  html += '<div class="reader-divider"></div>';
  visibleSections.forEach(function(sec) {
    if (!sec) return;
    html += '<section class="reader-section-block">';
    if (sec.heading) {
      var headingLevel = Math.min(6, Math.max(3, (parseInt(sec.level || 2, 10) || 2) + 1));
      html += '<h' + headingLevel + ' class="reader-section-title">' + esc(sec.heading) + "</h" + headingLevel + ">";
    }
    var paragraphIndex = 0;
    (sec.content || []).forEach(function(p) {
      var text = esc(p.text);
      if (!text) return;
      if (p.kind === "subheading") {
        html += '<h4 class="reader-subsection-title">' + text + "</h4>";
        return;
      }
      if (p.bold) text = "<strong>" + text + "</strong>";
      if (p.italic) text = "<em>" + text + "</em>";
      var paraClass = paragraphIndex === 0 ? "reader-para lead" : "reader-para";
      html += '<p class="' + paraClass + '">' + text + "</p>";
      paragraphIndex += 1;
    });
    html += "</section>";
  });
  html += "</div>";
  container.innerHTML = html;
  container.scrollTop = 0;
}

function closeTextbookReader() {
  navigateTo("textbooks");
}

// Reader overrides: use the optimized server-side textbook model directly.
function normalizeOptimizedReaderModel(rawContent) {
  var source = rawContent || {};
  var model = { id: source.id || "", title: source.title || "", chapters: [] };
  (source.chapters || []).forEach(function(ch, ci) {
    var chapter = {
      heading: String(ch.heading || ("第 " + (ci + 1) + " 章")).trim(),
      level: 1,
      chapterNo: ci + 1,
      sections: [],
    };
    (ch.sections || []).forEach(function(sec, si) {
      var section = {
        heading: String(sec.heading || (si === 0 ? "导读" : "延伸阅读")).trim(),
        level: sec.level || (sec.showInToc ? 2 : 3),
        showInToc: !!sec.showInToc,
        sectionNo: sec.sectionNo || "",
        index: chapter.sections.length,
        content: [],
      };
      (sec.content || []).forEach(function(item) {
        var text = String(item && item.text || "").replace(/\s+/g, " ").trim();
        if (!text) return;
        section.content.push({
          text: text,
          style: item.style || "Normal",
          level: item.level || 0,
          bold: !!item.bold,
          italic: !!item.italic,
          kind: item.kind || "",
        });
      });
      if (section.content.length) chapter.sections.push(section);
    });
    if (chapter.sections.length) model.chapters.push(chapter);
  });
  return model;
}

function createReaderModel(rawContent) {
  return normalizeOptimizedReaderModel(rawContent);
}

function getReaderChapterTitle(chapter, chapterIdx) {
  if (!chapter) return "第 " + (chapterIdx + 1) + " 章";
  var title = String(chapter.heading || "").trim();
  return title || ("第 " + (chapterIdx + 1) + " 章");
}

function syncReaderTocLayout() {
  var container = document.getElementById("reader-container");
  var btn = document.getElementById("reader-toc-toggle");
  if (container) container.classList.toggle("toc-collapsed", readerTocCollapsed);
  if (btn) {
    btn.textContent = readerTocCollapsed ? "显示目录" : "收起目录";
    btn.setAttribute("aria-expanded", readerTocCollapsed ? "false" : "true");
  }
}

function renderReaderToc() {
  var tocList = document.getElementById("toc-list");
  if (!tocList) return;
  tocList.innerHTML = "";

  var content = currentReaderModel || currentBookContent;
  if (!content || !content.chapters) return;

  content.chapters.forEach(function(ch, ci) {
    var group = document.createElement("li");
    var sections = Array.isArray(ch.sections) ? ch.sections.filter(function(sec) {
      return !!(sec && sec.showInToc && sec.heading && sec.content && sec.content.length);
    }) : [];
    var expanded = isReaderTocExpanded(ci);
    var chapterTitle = getReaderChapterTitle(ch, ci);
    var chapterActive = currentReaderState.chapterIdx === ci && currentReaderState.sectionIdx === -1;

    group.className = "toc-group" + (expanded ? " expanded" : "") + (currentReaderState.chapterIdx === ci ? " current-chapter" : "");
    group.dataset.chapter = String(ci);

    var row = document.createElement("div");
    row.className = "toc-group-row";

    var toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "toc-group-toggle";
    toggle.textContent = expanded ? "-" : "+";
    toggle.title = expanded ? "收起本章目录" : "展开本章目录";
    toggle.onclick = function(event) { toggleReaderChapterGroup(ci, event); };
    row.appendChild(toggle);

    var chapterBtn = document.createElement("button");
    chapterBtn.type = "button";
    chapterBtn.className = "toc-group-link" + (chapterActive ? " active" : "");
    chapterBtn.textContent = chapterTitle;
    chapterBtn.onclick = function() {
      ensureReaderChapterVisible(ci);
      renderChapter(ci, -1);
    };
    row.appendChild(chapterBtn);

    if (sections.length) {
      var meta = document.createElement("span");
      meta.className = "toc-group-meta";
      meta.textContent = sections.length + "节";
      row.appendChild(meta);
    }
    group.appendChild(row);

    if (sections.length) {
      var subList = document.createElement("ul");
      subList.className = "toc-section-list";
      subList.hidden = !expanded;
      sections.forEach(function(sec) {
        var sectionIndex = typeof sec.index === "number" ? sec.index : ch.sections.indexOf(sec);
        var item = document.createElement("li");
        var sectionActive = currentReaderState.chapterIdx === ci && currentReaderState.sectionIdx === sectionIndex;
        item.className = "toc-item toc-l" + (sec.level || 2) + (sectionActive ? " active" : "");
        item.dataset.chapter = String(ci);
        item.dataset.section = String(sectionIndex);

        var link = document.createElement("a");
        link.href = "javascript:void(0)";
        link.textContent = sec.heading || ("第 " + (sectionIndex + 1) + " 节");
        link.onclick = function() {
          ensureReaderChapterVisible(ci);
          renderChapter(ci, sectionIndex);
        };

        item.appendChild(link);
        subList.appendChild(item);
      });
      group.appendChild(subList);
    }
    tocList.appendChild(group);
  });

  scrollActiveReaderTocIntoView();
}

async function openTextbook(bookId, bookTitle) {
  try {
    var resp = await fetch("/api/textbooks/" + bookId + "/content", { headers: authHeaders() });
    if (!resp.ok) { alert("无法加载教材内容"); return; }
    currentBookContent = await resp.json();
    currentReaderModel = createReaderModel(currentBookContent);
    currentReaderState = { chapterIdx: 0, sectionIdx: -1 };
    currentBookTitle = bookTitle || currentReaderModel.title || currentBookContent.title || "教材阅读";
    navigateTo("textbook-reader");
    renderTextbookContent(currentBookTitle);
  } catch(err) {
    alert("加载失败: " + err.message);
  }
}

function renderTextbookContent(bookTitle) {
  currentBookTitle = bookTitle || currentBookTitle || "教材阅读";
  setReaderText("reader-title", currentBookTitle);
  setReaderText("reader-book-title", currentBookTitle);
  setReaderText("reader-kicker", "电子教材");
  readerTocCollapsed = false;
  readerTocExpandedChapters = {};
  syncReaderTocLayout();
  var rc = document.getElementById("reader-content");
  if (rc) rc.className = "reader-content";
  var model = currentReaderModel || currentBookContent;
  if (!model || !model.chapters) return;
  var chapterCount = model.chapters.length || 0;
  var sectionCount = model.chapters.reduce(function(total, ch) {
    return total + (ch.sections || []).filter(function(sec) { return sec.showInToc; }).length;
  }, 0);
  setReaderText("reader-meta-structure", chapterCount + " 章 · " + sectionCount + " 节");
  setReaderText("reader-book-subtitle", chapterCount ? "已按教材原文结构整理目录，可按章节目阅读" : "当前教材暂无可展示章节");
  setReaderText("reader-progress", chapterCount ? "第 1 章" : "未开始");
  if (chapterCount > 0) renderChapter(0, -1);
  else renderReaderToc();
}

function renderChapter(chapterIdx, sectionIdx) {
  var container = document.getElementById("reader-content");
  var model = currentReaderModel || currentBookContent;
  if (!container || !model || !model.chapters) return;
  var ch = model.chapters[chapterIdx];
  if (!ch) return;

  currentReaderState = { chapterIdx: chapterIdx, sectionIdx: sectionIdx };
  var chapterTitle = getReaderChapterTitle(ch, chapterIdx);
  var allSections = ch.sections || [];
  var visibleSections = allSections;
  var sectionTitle = "";
  if (sectionIdx >= 0) {
    visibleSections = [allSections[sectionIdx]];
    sectionTitle = allSections[sectionIdx] ? (allSections[sectionIdx].heading || "") : "";
  }

  setReaderText("reader-book-title", currentBookTitle || "教材阅读");
  setReaderText("reader-book-subtitle", sectionTitle || chapterTitle);
  setReaderText("reader-progress", "第 " + (chapterIdx + 1) + " 章");
  ensureReaderChapterVisible(chapterIdx);
  renderReaderToc();

  var html = "";
  html += '<div class="reader-book-shell">';
  html += '<div class="reader-book-head">';
  html += '<div class="reader-book-meta"><span class="reader-meta-pill">教材</span><span class="reader-meta-pill">第 ' + (chapterIdx + 1) + ' 章</span></div>';
  html += '<h2 class="reader-chapter-title">' + esc(chapterTitle) + "</h2>";
  html += '<div class="reader-book-subtitle">' + esc(sectionTitle || "按电子书样式整理后的阅读内容") + "</div>";
  html += "</div>";
  html += '<div class="reader-divider"></div>';

  visibleSections.forEach(function(sec) {
    if (!sec) return;
    html += '<section class="reader-section-block">';
    if (sec.heading && sec.heading !== "导读") {
      var headingLevel = Math.min(6, Math.max(3, (parseInt(sec.level || 2, 10) || 2) + 1));
      html += '<h' + headingLevel + ' class="reader-section-title">' + esc(sec.heading) + "</h" + headingLevel + ">";
    }
    var paragraphIndex = 0;
    (sec.content || []).forEach(function(p) {
      var text = esc(p.text);
      if (!text) return;
      if (p.kind === "subheading") {
        html += '<h4 class="reader-subsection-title">' + text + "</h4>";
        return;
      }
      if (p.bold) text = "<strong>" + text + "</strong>";
      if (p.italic) text = "<em>" + text + "</em>";
      var paraClass = paragraphIndex === 0 ? "reader-para lead" : "reader-para";
      html += '<p class="' + paraClass + '">' + text + "</p>";
      paragraphIndex += 1;
    });
    html += "</section>";
  });

  html += "</div>";
  container.innerHTML = html;
  container.scrollTop = 0;
}

// ─── 课件 ───
function renderCoursewareItem(d) {
 return `<div class="data-item"><div class="data-item-header">
   <div><div class="data-item-title">${esc(d.title)}</div>
   <div class="data-item-meta"><span>${esc(d.chapter)}</span>${d.description ? `<span>${esc(d.description)}</span>` : ""}${d.file_name ? `<span>${esc(d.file_name)}</span>` : ""}</div></div>
   <div class="data-item-actions">
     ${d.file_path ? `<a class="btn btn-sm" href="${esc(d.file_path)}" target="_blank" rel="noopener noreferrer">打开</a>` : ""}
     <button class="btn btn-danger btn-sm" onclick="deleteItem('/api/courseware','${d.id}','courseware-list',renderCoursewareItem)">删除</button>
   </div></div>
 </div>`;
}

function showCoursewareForm() { showForm("courseware-form"); }
function showCoursewareUploadForm() { showForm("courseware-upload-form"); }

async function saveCourseware() {
 const item = { title: g("cw-title"), chapter: g("cw-chapter"), description: g("cw-desc") };
 await api("/api/courseware", "POST", item);
 closeForm("courseware-form");
 fetchData("/api/courseware", "courseware-list", renderCoursewareItem);
}

async function uploadCoursewareFile() {
  var input = document.getElementById("cw-upload-file");
  if (!input || !input.files || !input.files[0]) {
    if (typeof showError === "function") showError("请先选择PPT文件");
    return;
  }
  var file = input.files[0];
  var lower = file.name.toLowerCase();
  if (!lower.endsWith(".ppt") && !lower.endsWith(".pptx")) {
    if (typeof showError === "function") showError("仅支持 .ppt 或 .pptx");
    return;
  }
  var reader = new FileReader();
  reader.onload = async function(ev) {
    try {
      var b64 = ev.target.result.split(",")[1];
      var result = await api("/api/courseware/upload", "POST", {
        filename: file.name,
        content: b64
      });
      closeForm("courseware-upload-form");
      input.value = "";
      fetchData("/api/courseware", "courseware-list", renderCoursewareItem);
      if (typeof showSuccess === "function") showSuccess(result && result.action === "replaced" ? "同名PPT已覆盖更新" : "PPT导入完成");
      if (result && result.item && result.item.file_path) {
        window.open(result.item.file_path, "_blank");
      }
    } catch (err) {
      if (typeof showError === "function") showError("PPT导入失败：" + err.message);
    }
  };
  reader.readAsDataURL(file);
}

// ─── 教学大纲 ───
function renderSyllabusItem(d) {
 return `<div class="data-item"><div class="data-item-header">
   <div><div class="data-item-title">${esc(d.title)}</div>
   <div class="data-item-meta"><span>${esc(d.semester)}</span>${d.total_hours ? `<span>${d.total_hours} 学时</span>` : ""}</div></div>
   <div class="data-item-actions">
     <button class="btn btn-danger btn-sm" onclick="deleteItem('/api/syllabus','${d.id}','syllabus-list',renderSyllabusItem)">删除</button>
   </div></div>
   ${d.content ? `<div class="data-item-body">${esc(d.content).replace(/\n/g, "<br>")}</div>` : ""}
 </div>`;
}

function showSyllabusForm() { showForm("syllabus-form"); }

async function saveSyllabus() {
 const item = { title: g("sy-title"), semester: g("sy-semester"), total_hours: parseInt(g("sy-hours")) || 0, content: g("sy-content") };
 await api("/api/syllabus", "POST", item);
 closeForm("syllabus-form");
 fetchData("/api/syllabus", "syllabus-list", renderSyllabusItem);
}

// ─── 参考书目 ───
function renderReferenceItem(d) {
 return `<div class="data-item"><div class="data-item-header">
   <div><div class="data-item-title">${esc(d.title)}</div>
   <div class="data-item-meta"><span>${esc(d.author)}</span><span>${esc(d.publisher)}</span><span>${esc(d.year)}</span></div></div>
   <div class="data-item-actions">
     <button class="btn btn-danger btn-sm" onclick="deleteItem('/api/references','${d.id}','reference-list',renderReferenceItem)">删除</button>
   </div></div>
   ${d.description ? `<div class="data-item-body">${esc(d.description)}</div>` : ""}
 </div>`;
}

function showReferenceForm() { showForm("reference-form"); }

async function saveReference() {
 const item = { title: g("ref-title"), author: g("ref-author"), publisher: g("ref-publisher"), year: g("ref-year"), isbn: g("ref-isbn"), description: g("ref-desc") };
 await api("/api/references", "POST", item);
 closeForm("reference-form");
 fetchData("/api/references", "reference-list", renderReferenceItem);
}

window.toggleReaderToc = toggleReaderToc;
window.showCoursewareUploadForm = showCoursewareUploadForm;
window.uploadCoursewareFile = uploadCoursewareFile;
