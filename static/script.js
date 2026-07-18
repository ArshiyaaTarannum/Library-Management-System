// ================= SEARCH =================

const searchIcon = document.getElementById("search-icon");
const searchBox = document.getElementById("search-box");

if (searchIcon && searchBox) {

    searchIcon.addEventListener("click", function () {

        searchBox.classList.toggle("show");

    });

    document.addEventListener("click", function (e) {

        if (
            !searchBox.contains(e.target) &&
            !searchIcon.contains(e.target)
        ) {

            searchBox.classList.remove("show");

        }

    });

}

// ================= FLASH MESSAGE =================

setTimeout(function () {

    const flash = document.querySelector(".flash-message");

    if (flash) {

        flash.style.display = "none";

    }

}, 3000);

// ================= BOOK =================

// ================= BOOK =================

function loadBook(
    id,
    name,
    author,
    categoryId,
    publication,
    publicationDate,
    entryDate,
    language,
    edition,
    purchasePrice
) {


    document.getElementById("book_id").value = id;

    document.getElementById("display_book_id").value = id;


    document.getElementById("book_name").value = name;

    document.getElementById("author").value = author;

    document.getElementById("category_id").value = categoryId;

    document.getElementById("publication").value = publication;


    document.getElementById("publication_date").value = publicationDate;

    document.getElementById("entry_date").value = entryDate;


    document.getElementById("language").value = language;

    document.getElementById("edition").value = edition;

    document.getElementById("purchase_price").value = purchasePrice;


    // Editing a Book's details never creates or changes BookCopy records,
    // so the Total Copies field and the whole copy-allocation workflow
    // are hidden while editing (see the "add-only" elements in
    // add_books.html and setAddOnlyVisible() below).
    setAddOnlyVisible(false);


    document.getElementById("book-form").action = "/update_book";


    document.getElementById("save-btn").innerHTML = "Update Book";


}

function resetBookForm() {

    document.getElementById("book-form").reset();

    document.getElementById("book-form").action = "/add_book";

    document.getElementById("save-btn").innerHTML = "Save Book";

    document.getElementById("book_id").value = "";

    document.getElementById("entry_date").value =
        new Date().toISOString().split("T")[0];

    // static/script.js is never passed through Jinja, so the next Book ID
    // has to come from the data-next-id attribute the template already
    // renders onto this field, not from "{{ next_book_id }}" written here.
    const displayBookId = document.getElementById("display_book_id");
    displayBookId.value = displayBookId.dataset.nextId;

    // Back to "Add" mode: bring back Total Copies + the allocation workflow,
    // and clear out whatever groups/selection were previously built.
    setAddOnlyVisible(true);
    resetCopyAllocationUI();

}

// ================= ADD BOOK: COPY ALLOCATION WORKFLOW =================
//
// Handles Step 2 of the Add Book form: after Total Copies is entered,
// the librarian is asked whether every copy shares the same condition.
//   - Yes -> one common Shelf/Condition/Remark applied to all copies.
//   - No  -> repeatable grouped blocks, validated to sum exactly to
//            Total Copies before the form can be submitted.
// The same mechanism serves both small (<=25) and large (>25) batches;
// past 25 copies a hint simply recommends grouping, nothing else changes.

// Must stay in sync with VALID_CONDITIONS in app.py.
const CONDITION_OPTIONS = ["Excellent", "Good", "Fair", "Worn", "Damaged", "Other"];

function buildOptionsHTML(values, placeholder) {

    let html = `<option value="">${placeholder}</option>`;

    values.forEach(function (value) {
        html += `<option value="${value}">${value}</option>`;
    });

    return html;
}

function setAddOnlyVisible(visible) {

    document.querySelectorAll(".add-only").forEach(function (el) {
        el.style.display = visible ? "" : "none";
    });

    const totalCopiesInput = document.getElementById("total_copies");

    if (totalCopiesInput) {
        totalCopiesInput.required = visible;
    }
}

let groupCounter = 0;

function createGroupRow() {

    groupCounter += 1;

    const row = document.createElement("div");
    row.className = "copy-group";

    row.innerHTML = `
        <div class="copy-group-header">
            <span>Group ${groupCounter}</span>
            <button type="button" class="remove-group-btn delete-btn">Remove</button>
        </div>

        <label>Number of Copies</label>
        <input type="number" class="group-quantity" min="1" value="1">

        <label>Shelf</label>
        <input type="text" class="group-shelf" placeholder="e.g. A2">

        <label>Condition</label>
        <select class="group-condition">
            <option value="Excellent" selected>Excellent</option>
            <option value="Good">Good</option>
            <option value="Fair">Fair</option>
            <option value="Worn">Worn</option>
            <option value="Damaged">Damaged</option>
            <option value="Other">Other</option>
        </select>

        <label>Additional Remark (optional)</label>
        <input type="text" class="group-remark" placeholder="e.g. Slightly worn">
    `;

    row.querySelector(".remove-group-btn").addEventListener(
        "click",
        function () {
            row.remove();
            updateAllocationSummary();
        }
    );

    return row;
}

function updateAllocationSummary() {

    const totalCopiesInput = document.getElementById("total_copies");
    const groupList = document.getElementById("group-list");
    const allocatedCountEl = document.getElementById("allocated-count");
    const totalCountEl = document.getElementById("total-count");
    const allocationError = document.getElementById("allocation-error");

    const total = parseInt(totalCopiesInput.value, 10) || 0;
    totalCountEl.textContent = total;

    let allocated = 0;

    groupList.querySelectorAll(".group-quantity").forEach(function (input) {
        allocated += parseInt(input.value, 10) || 0;
    });

    allocatedCountEl.textContent = allocated;

    if (allocated === total && total > 0) {

        allocatedCountEl.style.color = "#198754";
        allocationError.style.display = "none";

    } else {

        allocatedCountEl.style.color = "#dc3545";

        if (allocated > total) {
            allocationError.textContent =
                `Allocated copies (${allocated}) exceed Total Copies (${total}).`;
        } else {
            allocationError.textContent =
                `Allocated copies (${allocated}) are less than Total Copies (${total}).`;
        }

        allocationError.style.display = "block";
    }
}

function isAllocationValid() {

    const totalCopiesInput = document.getElementById("total_copies");
    const groupList = document.getElementById("group-list");

    const total = parseInt(totalCopiesInput.value, 10) || 0;

    let allocated = 0;

    groupList.querySelectorAll(".group-quantity").forEach(function (input) {
        allocated += parseInt(input.value, 10) || 0;
    });

    return total > 0 && allocated === total;
}

function resetCopyAllocationUI() {

    const sameYes = document.getElementById("same_condition_yes");
    const sameNo = document.getElementById("same_condition_no");
    const commonForm = document.getElementById("common-form");
    const groupedForm = document.getElementById("grouped-form");
    const groupList = document.getElementById("group-list");

    if (!sameYes) return;

    sameYes.checked = false;
    sameNo.checked = false;
    commonForm.style.display = "none";
    groupedForm.style.display = "none";
    groupList.innerHTML = "";
    groupCounter = 0;

    updateAllocationSummary();
    refreshLargeBatchHint();
}

function refreshLargeBatchHint() {

    const totalCopiesInput = document.getElementById("total_copies");
    const largeBatchHint = document.getElementById("large-batch-hint");

    if (!totalCopiesInput || !largeBatchHint) return;

    const total = parseInt(totalCopiesInput.value, 10) || 0;
    largeBatchHint.style.display = total > 25 ? "block" : "none";
}

function initAddBookWorkflow() {

    const bookForm = document.getElementById("book-form");
    const totalCopiesInput = document.getElementById("total_copies");

    if (!bookForm || !totalCopiesInput) return;

    const sameYes = document.getElementById("same_condition_yes");
    const sameNo = document.getElementById("same_condition_no");
    const commonForm = document.getElementById("common-form");
    const groupedForm = document.getElementById("grouped-form");
    const groupList = document.getElementById("group-list");
    const addGroupBtn = document.getElementById("add-group-btn");
    const copyGroupsField = document.getElementById("copy_groups");

    // Populate the common-form dropdowns once, from the same option
    // lists used to build every dynamically created group row.

    const commonCondition = document.getElementById("common_condition");
    commonCondition.innerHTML = `
    <option value="Excellent" selected>Excellent</option>
    <option value="Good">Good</option>
    <option value="Fair">Fair</option>
    <option value="Worn">Worn</option>
    <option value="Damaged">Damaged</option>
    <option value="Other">Other</option>
    `;

    totalCopiesInput.addEventListener("input", function () {
        refreshLargeBatchHint();
        resetCopyAllocationUI();
    });

    sameYes.addEventListener("change", function () {
        commonForm.style.display = "block";
        groupedForm.style.display = "none";
    });

    sameNo.addEventListener("change", function () {

        commonForm.style.display = "none";
        groupedForm.style.display = "block";

        if (groupList.children.length === 0) {
            groupList.appendChild(createGroupRow());
        }

        updateAllocationSummary();
    });

    addGroupBtn.addEventListener("click", function () {
        groupList.appendChild(createGroupRow());
        updateAllocationSummary();
    });

    // Event delegation: catches quantity changes on every group row,
    // including ones added later, without re-binding listeners each time.
    groupList.addEventListener("input", function (e) {
        if (e.target.classList.contains("group-quantity")) {
            updateAllocationSummary();
        }
    });

    bookForm.addEventListener("submit", function (e) {

        // Editing an existing book never touches BookCopy records -
        // let it submit as a normal Book update.
        if (bookForm.action.indexOf("/update_book") !== -1) {
            return;
        }

        const total = parseInt(totalCopiesInput.value, 10) || 0;

        if (total < 1) {
            e.preventDefault();
            alert("Please enter a valid number of Total Copies.");
            return;
        }

        let groups = [];

        if (sameYes.checked) {

            const shelf = document.getElementById("common_shelf").value.trim();
            const condition = document.getElementById("common_condition").value;
            const remark = document.getElementById("common_remark").value.trim();

            if (!shelf || !condition) {
                e.preventDefault();
                alert("Please fill Shelf and Condition section.");
                return;
            }

            groups = [{
                quantity: total,
                shelf: shelf,
                status: "Available",
                condition: condition,
                remark: remark
            }];

        } else if (sameNo.checked) {

            if (!isAllocationValid()) {
                e.preventDefault();
                updateAllocationSummary();
                alert("Allocated copies must exactly equal Total Copies before saving.");
                return;
            }

            const rows = groupList.querySelectorAll(".copy-group");

            for (const row of rows) {

                const quantity = parseInt(row.querySelector(".group-quantity").value, 10) || 0;
                const shelf = row.querySelector(".group-shelf").value.trim();
                const condition = row.querySelector(".group-condition").value;
                const remark = row.querySelector(".group-remark").value.trim();

                if (quantity < 1 || !shelf || !condition) {
                    e.preventDefault();
                    alert("Every group needs a valid Number of Copies, Shelf and Condition.");
                    return;
                }

                groups.push({
                    quantity: quantity,
                    shelf: shelf,
                    status: "Available",
                    condition: condition,
                    remark: remark
                });
            }

        } else {

            e.preventDefault();
            alert("Please select whether all copies have the same condition.");
            return;
        }

        copyGroupsField.value = JSON.stringify(groups);
    });

    refreshLargeBatchHint();
}

document.addEventListener("DOMContentLoaded", initAddBookWorkflow);

// ================= CATEGORY =================

function loadCategory(id, name) {

    document.getElementById("category_id").value = id;

    document.getElementById("category_name").value = name;

    document.getElementById("category-form").action = "/update_category";

    document.getElementById("save-category").innerHTML = "Update Category";

}

function resetCategoryForm() {

    document.getElementById("category-form").reset();

    document.getElementById("category-form").action = "/add_category";

    document.getElementById("save-category").innerHTML = "Save Category";

    document.getElementById("category_id").value = "";

}

// ================= BORROW =================

function loadBorrow(
    issueId,
    bookId,
    studentName,
    studentId,
    issueDate,
    dueDate,
    returnDate,
    entryDate,
    status
) {

    document.getElementById("issue_id").value = issueId;

    document.getElementById("display_issue_id").value = issueId;

    document.getElementById("book_id").value = bookId;

    document.getElementById("student_name").value = studentName;

    document.getElementById("student_id").value = studentId;

    document.getElementById("issue_date").value = issueDate;

    document.getElementById("due_date").value = dueDate;

    document.getElementById("return_date").value = returnDate || "";

    document.getElementById("entry_date").value = entryDate;

    document.getElementById("borrow-form").action = "/update_borrow";

    document.getElementById("save-borrow").innerHTML = "Update Record";

}

function resetBorrowForm() {

    document.getElementById("borrow-form").reset();

    document.getElementById("borrow-form").action = "/borrow_book";

    document.getElementById("save-borrow").innerHTML = "Issue Book";

    document.getElementById("issue_id").value = "";

    document.getElementById("entry_date").value =
        new Date().toISOString().split("T")[0];

    document.getElementById("status").value = "Issued";

}

// ================= ENTER KEY =================

document.addEventListener("keydown", function (e) {

    if (e.key !== "Enter") return;

    const bookForm = document.getElementById("book-form");
    const categoryForm = document.getElementById("category-form");
    const borrowForm = document.getElementById("borrow-form");

    if (bookForm) {

        e.preventDefault();
        bookForm.requestSubmit();

    }

    else if (categoryForm) {

        e.preventDefault();
        categoryForm.requestSubmit();

    }

    else if (borrowForm) {

        e.preventDefault();
        borrowForm.requestSubmit();

    }

});

// ================= ESC KEY =================

document.addEventListener("keydown", function (e) {

    if (e.key !== "Escape") return;

    const bookForm = document.getElementById("book-form");
    const categoryForm = document.getElementById("category-form");
    const borrowForm = document.getElementById("borrow-form");

    if (bookForm) {

        resetBookForm();

    }

    else if (categoryForm) {

        resetCategoryForm();

    }

    else if (borrowForm) {

        resetBorrowForm();

    }

});

function editCopy(copyId, shelf, status, condition, remark) {

    document.getElementById("edit_copy_id").value = copyId;
    document.getElementById("edit_shelf").value = shelf;
    document.getElementById("edit_status").value = status;
    document.getElementById("edit_condition").value = condition;
    document.getElementById("edit_remark").value = remark;

    document.getElementById("edit_copy_id").scrollIntoView({
        behavior: "smooth",
        block: "center"
    });

}