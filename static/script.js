const searchIcon = document.getElementById("search-icon");
const searchBox = document.getElementById("search-box");

if (searchIcon && searchBox) {

    searchIcon.addEventListener("click", function () {

        searchBox.classList.toggle("show");

    });

}

setTimeout(function () {

    const flash = document.querySelector(".flash-message");

    if (flash) {

        flash.style.display = "none";

    }

}, 3000);

function loadBook(
    id,
    name,
    author,
    categoryId,
    publication,
    publicationDate,
    entryDate
){

    document.getElementById("book_id").value = id;
    document.getElementById("display_book_id").value = id;

    document.getElementById("book_name").value = name;
    document.getElementById("author").value = author;
    document.getElementById("category_id").value = categoryId;
    document.getElementById("publication").value = publication;
    document.getElementById("publication_date").value = publicationDate;
    document.getElementById("entry_date").value = entryDate;

    document.getElementById("book-form").action = "/update_book";
    document.getElementById("save-btn").innerHTML = "Update Book";
}

function resetBookForm(){

    document.getElementById("book-form").reset();

    document.getElementById("book-form").action = "/add_book";

    document.getElementById("save-btn").innerHTML = "Save Book";

    document.getElementById("book_id").value = "";

    document.getElementById("display_book_id").value = "";

    document.getElementById("entry_date").value = new Date().toISOString().split("T")[0];

}
function loadCategory(id, name){

    document.getElementById("category_id").value = id;

    document.getElementById("category_name").value = name;

    document.getElementById("category-form").action = "/update_category";

    document.getElementById("save-category").innerHTML = "Update Category";

}

function resetCategoryForm(){

    document.getElementById("category-form").reset();

    document.getElementById("category-form").action = "/add_category";

    document.getElementById("save-category").innerHTML = "Save Category";

    document.getElementById("category_id").value = "";

}
document.addEventListener("keydown", function (e) {

    if (e.key !== "Enter") return;

    const bookForm = document.getElementById("book-form");
    const categoryForm = document.getElementById("category-form");

    if (bookForm) {

        e.preventDefault();
        bookForm.requestSubmit();

    }

    else if (categoryForm) {

        e.preventDefault();
        categoryForm.requestSubmit();

    }

});