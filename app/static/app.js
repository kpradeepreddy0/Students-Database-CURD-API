const rowsElement = document.querySelector("#student-rows");
const searchInput = document.querySelector("#search");
const courseFilter = document.querySelector("#course-filter");
const dialog = document.querySelector("#student-dialog");
const form = document.querySelector("#student-form");
const formError = document.querySelector("#form-error");
const toast = document.querySelector("#toast");
const askForm = document.querySelector("#ask-form");
const askQuestion = document.querySelector("#ask-question");
const askResult = document.querySelector("#ask-result");
const askAnswer = document.querySelector("#ask-answer");
const askMeta = document.querySelector("#ask-meta");

let students = [];
let editingId = null;
let toastTimer;

const icons = () => window.lucide?.createIcons({ attrs: { "stroke-width": 1.8 } });

function formatDate(value) {
  if (!value) return "Not set";
  const [year, month, day] = value.split("-").map(Number);
  return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", year: "numeric" }).format(new Date(year, month - 1, day));
}

function initials(name) {
  return name.trim().split(/\s+/).slice(0, 2).map((part) => part[0]).join("").toUpperCase();
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("visible");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("visible"), 2800);
}

function setError(message) {
  formError.textContent = message;
  formError.hidden = !message;
}

function detailMessage(detail) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((item) => item.msg).join(". ");
  return "Please check the details and try again.";
}

function filteredStudents() {
  const query = searchInput.value.trim().toLocaleLowerCase();
  const course = courseFilter.value;
  return students.filter((student) => {
    const matchesQuery = !query || `${student.name} ${student.course || ""} ${student.email || ""} ${student.phone || ""}`.toLocaleLowerCase().includes(query);
    return matchesQuery && (!course || student.course === course);
  });
}

function makeAction(label, iconName, className, handler) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = `row-action ${className}`;
  button.title = label;
  button.setAttribute("aria-label", label);
  button.innerHTML = `<i data-lucide="${iconName}"></i>`;
  button.addEventListener("click", handler);
  return button;
}

function renderRows() {
  const visible = filteredStudents();
  rowsElement.replaceChildren();
  document.querySelector("#visible-count").textContent = visible.length;
  document.querySelector("#table-summary").textContent = `Showing ${visible.length} of ${students.length} ${students.length === 1 ? "student" : "students"}`;

  for (const student of visible) {
    const row = document.createElement("tr");
    const studentCell = document.createElement("td");
    const identity = document.createElement("div");
    identity.className = "student-cell";
    const avatar = document.createElement("span");
    avatar.className = `student-avatar tone-${student.id % 4}`;
    avatar.textContent = initials(student.name);
    const nameBlock = document.createElement("div");
    const name = document.createElement("div");
    name.className = "student-name";
    name.textContent = student.name;
    const id = document.createElement("div");
    id.className = "student-id";
    id.textContent = `STU-${String(student.id).padStart(4, "0")}`;
    nameBlock.append(name, id);
    identity.append(avatar, nameBlock);
    studentCell.append(identity);

    const courseCell = document.createElement("td");
    if (student.course) {
      const tag = document.createElement("span");
      tag.className = "course-tag";
      tag.textContent = student.course;
      courseCell.append(tag);
    } else {
      courseCell.textContent = "Not set";
    }

    const enrolledCell = document.createElement("td");
    enrolledCell.textContent = formatDate(student.enrollment_date);
    const contactCell = document.createElement("td");
    contactCell.className = "contact-cell";
    contactCell.textContent = student.email || student.phone || "Not set";
    const actionCell = document.createElement("td");
    const actions = document.createElement("div");
    actions.className = "action-cell";
    actions.append(
      makeAction("Edit student", "pencil", "", () => openDialog(student)),
      makeAction("Delete student", "trash-2", "delete", () => removeStudent(student)),
    );
    actionCell.append(actions);
    row.append(studentCell, courseCell, enrolledCell, contactCell, actionCell);
    rowsElement.append(row);
  }

  const empty = visible.length === 0;
  document.querySelector("#empty-state").hidden = !empty;
  document.querySelector("#empty-title").textContent = students.length === 0 ? "No students yet" : "No matching students";
  document.querySelector("#empty-copy").textContent = students.length === 0
    ? "The directory is ready for its first record."
    : "Try another name or course filter.";
  document.querySelector("#empty-add").hidden = students.length !== 0;
  icons();
}

function renderCourses() {
  const courseCounts = new Map();
  for (const student of students) {
    const course = student.course?.trim();
    if (course) courseCounts.set(course, (courseCounts.get(course) || 0) + 1);
  }
  const courses = [...courseCounts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  const list = document.querySelector("#course-list");
  list.replaceChildren();
  document.querySelector("#course-empty").hidden = courses.length > 0;
  for (const [index, [course, count]] of courses.slice(0, 5).entries()) {
    const item = document.createElement("div");
    const heading = document.createElement("div");
    heading.className = "course-item-head";
    const label = document.createElement("span");
    label.textContent = course;
    const value = document.createElement("strong");
    value.textContent = count;
    heading.append(label, value);
    const track = document.createElement("div");
    track.className = "course-track";
    track.setAttribute("role", "meter");
    track.setAttribute("aria-label", `${course}: ${count} students`);
    const bar = document.createElement("div");
    bar.className = `course-bar tone-${index % 5}`;
    bar.style.width = `${Math.max(8, (count / students.length) * 100)}%`;
    track.append(bar);
    item.append(heading, track);
    list.append(item);
  }

  const selected = courseFilter.value;
  courseFilter.replaceChildren(new Option("All courses", ""));
  for (const [course] of courses) courseFilter.add(new Option(course, course));
  if (courses.some(([course]) => course === selected)) courseFilter.value = selected;
}

function renderMetrics() {
  const courses = new Set(students.map((student) => student.course?.trim()).filter(Boolean));
  const now = new Date();
  const enrolledThisMonth = students.filter((student) => {
    if (!student.enrollment_date) return false;
    const enrolled = new Date(`${student.enrollment_date}T00:00:00`);
    return enrolled.getFullYear() === now.getFullYear() && enrolled.getMonth() === now.getMonth();
  }).length;
  const withEmail = students.filter((student) => student.email).length;
  document.querySelector("#total-students").textContent = students.length;
  document.querySelector("#course-count").textContent = courses.size;
  document.querySelector("#month-count").textContent = enrolledThisMonth;
  document.querySelector("#contact-rate").textContent = students.length ? Math.round((withEmail / students.length) * 100) : 0;
  const monthName = new Intl.DateTimeFormat(undefined, { month: "long" }).format(now);
  document.querySelector("#month-label").textContent = `New enrollments in ${monthName}`;
}

async function loadStudents() {
  const refresh = document.querySelector("#refresh");
  refresh.classList.add("is-loading");
  try {
    const response = await fetch("/students?limit=500");
    if (!response.ok) throw new Error("Could not load student records.");
    students = await response.json();
    renderMetrics();
    renderCourses();
    renderRows();
  } catch (error) {
    showToast(error.message || "Could not connect to the student directory.");
  } finally {
    refresh.classList.remove("is-loading");
  }
}

function openDialog(student = null) {
  editingId = student?.id ?? null;
  form.reset();
  setError("");
  document.querySelector("#dialog-eyebrow").textContent = student ? "UPDATE RECORD" : "NEW RECORD";
  document.querySelector("#dialog-title").textContent = student ? "Edit student" : "Add a student";
  document.querySelector("#save-student span").textContent = student ? "Save changes" : "Save record";
  if (student) {
    for (const [key, value] of Object.entries(student)) {
      const field = form.elements.namedItem(key);
      if (field) field.value = value ?? "";
    }
  }
  dialog.showModal();
  form.elements.namedItem("name").focus();
}

async function removeStudent(student) {
  if (!window.confirm(`Remove ${student.name} from the directory? This cannot be undone.`)) return;
  try {
    const response = await fetch(`/students/${student.id}`, { method: "DELETE" });
    if (!response.ok) throw new Error("Could not delete this student.");
    showToast(`${student.name} was removed.`);
    await loadStudents();
  } catch (error) {
    showToast(error.message || "Could not delete this student.");
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  setError("");
  const data = Object.fromEntries(new FormData(form));
  for (const key of ["email", "phone", "course", "address", "enrollment_date"]) data[key] = data[key]?.trim() || null;
  if (!data.email && !data.phone) {
    setError("Add an email address or phone number before saving.");
    return;
  }

  const saveButton = document.querySelector("#save-student");
  saveButton.disabled = true;
  try {
    const response = await fetch(editingId ? `/students/${editingId}` : "/students", {
      method: editingId ? "PATCH" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(detailMessage(result.detail));
    dialog.close();
    showToast(editingId ? "Student record updated." : "Student added to the directory.");
    await loadStudents();
  } catch (error) {
    setError(error.message || "Could not save this student.");
  } finally {
    saveButton.disabled = false;
  }
});

askForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const submitButton = document.querySelector("#ask-submit");
  submitButton.disabled = true;
  submitButton.classList.add("is-loading");
  askResult.hidden = true;
  askResult.classList.remove("has-error");

  try {
    const response = await fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: askQuestion.value.trim() }),
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(detailMessage(result.detail));
    askAnswer.textContent = result.answer;
    askMeta.textContent = `${result.model} · ${result.records_used} records`;
  } catch (error) {
    askAnswer.textContent = error.message || "Could not reach Ollama.";
    askMeta.textContent = "Check that Ollama is running and the configured model is installed.";
    askResult.classList.add("has-error");
  } finally {
    askResult.hidden = false;
    submitButton.disabled = false;
    submitButton.classList.remove("is-loading");
  }
});

document.querySelector("#add-student").addEventListener("click", () => openDialog());
document.querySelector("#empty-add").addEventListener("click", () => openDialog());
document.querySelector("#close-dialog").addEventListener("click", () => dialog.close());
document.querySelector("#cancel-dialog").addEventListener("click", () => dialog.close());
document.querySelector("#refresh").addEventListener("click", loadStudents);
searchInput.addEventListener("input", renderRows);
courseFilter.addEventListener("change", renderRows);

document.querySelector("#today").textContent = new Intl.DateTimeFormat(undefined, {
  weekday: "short", month: "short", day: "numeric",
}).format(new Date());
icons();
loadStudents();