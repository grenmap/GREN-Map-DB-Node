(function () {
    /**
     * Event handler for the "import rulesets" button
     * (change_list_object_tools.html).
     */
    function showFileInput() {
        let fileInput = document.getElementById("file-input");
        fileInput.click();
    }

    /**
     * Event handler for the file chooser input element
     * in the overriden rulesets page.
     */
    function importFile() {
        const form = document.getElementById("file-upload");
        form.submit();
    }

    // add onclick listener to import-ruleset
    let importRuleset = document.getElementById("import-ruleset");
    importRuleset.addEventListener("click", showFileInput);

    // add onchange listener to file-input
    let fileInput = document.getElementById("file-input");
    fileInput.addEventListener("change", importFile);
}());
