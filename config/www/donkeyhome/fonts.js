// Loads the DonkeyHome fonts (fonts.css next to this file) into Home Assistant's page.
// Loaded by `frontend: extra_module_url` in configuration.yaml, so no dashboard resources are needed.
if (!document.getElementById("donkeyhome-fonts")) {
  const link = document.createElement("link");
  link.id = "donkeyhome-fonts";
  link.rel = "stylesheet";
  link.href = new URL("fonts.css", import.meta.url).href;
  document.head.append(link);
}
