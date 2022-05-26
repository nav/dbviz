// Table selection dropdown
document.addEventListener("DOMContentLoaded", function (event) {
  var $form = $("#table-form");
  var $element = $("#select-table");
  if ($form) {
    $element.select2();
    $element.on("select2:select", function (e) {
      $form.submit();
    });
  }
});

// Colour mode change
function updateColourMode(event) {
  fetch("/colour-mode", { method: "POST" }).then(response =>  location.reload());
}
const changeColourModeButton = document.getElementById("change-colour-mode");
changeColourModeButton.onclick = updateColourMode;
