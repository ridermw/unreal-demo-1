"use strict";
const byId = id => document.getElementById(id);
let rounds = [];
function showRound(id) {
  const round = rounds.find(item => item.id === id);
  if (!round) throw new Error("Requested round is unavailable.");
  byId("actual").src = round.image;
  byId("status").textContent = round.accepted ? "Accepted visual + performance gates" : "Work in progress - not accepted";
  byId("assessment").textContent = round.assessment;
  byId("metrics").replaceChildren();
  for (const [label, value, max] of [
    ["Total", round.total, 10], ["Composition", round.scores.composition, 3],
    ["Lighting", round.scores.lighting, 3], ["Materials", round.scores.materials, 3],
    ["Details", round.scores.details, 1]
  ]) {
    const card = document.createElement("div");
    card.className = "metric";
    const number = document.createElement("strong");
    number.textContent = `${value} / ${max}`;
    const name = document.createElement("span");
    name.textContent = label;
    card.append(number, name);
    byId("metrics").append(card);
  }
  byId("fixes").replaceChildren();
  for (const fix of round.fixes) {
    const item = document.createElement("li");
    item.textContent = typeof fix === "string" ? fix : [fix.title, fix.action || fix.description].filter(Boolean).join(": ");
    byId("fixes").append(item);
  }
  const perf = round.performance;
  byId("performance").textContent = perf?.status === "success"
    ? `${round.matching_capture_and_performance ? "Verified same-state measurement" : "Recorded timing; exact capture/runtime match not verified"}: ${perf.median_fps.toFixed(2)} median FPS; ${perf.p95_frame_ms.toFixed(2)} ms p95. ${perf.resolution.join(" x ")}. ${perf.quality}. ${perf.frame_cap == null ? "Frame cap unverified." : perf.frame_cap ? `Frame cap ${perf.frame_cap} FPS.` : "Uncapped."} ${perf.one_frame_thread_lag == null ? "Thread-lag setting unverified." : perf.one_frame_thread_lag === false ? "One-frame thread lag disabled." : "One-frame thread lag enabled."} Numeric timing target ${perf.meets_target ? "passed" : "not met"}.`
    : "Performance has not yet been validly measured for this exact round. Earlier measurements are not treated as current.";
  byId("provenance").textContent = `${round.id} | Actual Unreal PNG SHA-256: ${round.sha256}`;
  const audit = round.component_audit || [];
  byId("component-section").hidden = !audit.length;
  byId("components").replaceChildren();
  for (const entry of audit) {
    const details = document.createElement("details");
    const summary = document.createElement("summary");
    summary.textContent = `${entry.id} - ${entry.status} (${entry.severity})`;
    details.append(summary);
    for (const [label, text] of [["Target", entry.target_observation], ["Unreal", entry.actual_observation],
                                  ["Correction", entry.correction]]) {
      const p = document.createElement("p");
      p.textContent = `${label}: ${text || "None"}`;
      details.append(p);
    }
    byId("components").append(details);
  }
}
byId("round").addEventListener("change", event => showRound(event.target.value));
byId("target-toggle").addEventListener("click", () => {
  const enabled = byId("target").hidden;
  byId("target").hidden = !enabled;
  byId("comparison").hidden = !enabled;
  byId("target-toggle").textContent = enabled ? "Show Unreal only" : "Compare with target";
  byId("image-label").textContent = enabled ? "LEFT: ACTUAL UNREAL / RIGHT: GENERATED TARGET" : "ACTUAL UNREAL CAPTURE";
});
byId("split").addEventListener("input", event => {
  byId("target").style.clipPath = `inset(0 0 0 ${event.target.value}%)`;
});
fetch("rounds.json").then(response => {
  if (!response.ok) throw new Error(`Evidence request failed (${response.status})`);
  return response.json();
}).then(data => {
  if (!Array.isArray(data) || !data.length) throw new Error("No judged round has been published.");
  rounds = data;
  for (const round of [...rounds].reverse()) {
    const option = document.createElement("option");
    option.value = round.id;
    option.textContent = `${round.id} - ${round.total}/10`;
    byId("round").append(option);
  }
  showRound(rounds.at(-1).id);
}).catch(error => {
  byId("status").textContent = "Evidence unavailable";
  byId("error").hidden = false;
  byId("error").textContent = error.message;
});
fetch("inspections.json").then(response => {
  if (!response.ok) throw new Error(`Inspection request failed (${response.status})`);
  return response.json();
}).then(inspections => {
  if (!Array.isArray(inspections)) throw new Error("Invalid inspection evidence.");
  byId("inspection-section").hidden = !inspections.length;
  for (const inspection of inspections) {
    const link = document.createElement("a");
    link.href = inspection.image;
    const image = document.createElement("img");
    image.src = inspection.image;
    image.alt = `Actual Unreal inspection: ${inspection.view}`;
    image.loading = "lazy";
    const label = document.createElement("strong");
    label.textContent = `${inspection.view} - ${inspection.fov} degree view`;
    link.append(image, label);
    byId("inspections").append(link);
  }
}).catch(error => {
  byId("error").hidden = false;
  byId("error").textContent += ` ${error.message}`;
});
