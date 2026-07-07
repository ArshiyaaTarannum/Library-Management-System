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
    category,
    publication,
    date
){

    document.getElementById("book_id").value = id;
    document.getElementById("display_book_id").value = id;
    document.getElementById("book_name").value = name;
    document.getElementById("author").value = author;
    document.getElementById("category_id").value = category;
    document.getElementById("publication").value = publication;
    document.getElementById("publication_date").value = date;

    document.getElementById("book-form").action = "/update_book";

    document.getElementById("save-btn").innerHTML = "Update Book";

}

function resetBookForm(){

    document.getElementById("book-form").reset();

    document.getElementById("book-form").action = "/add_book";

    document.getElementById("save-btn").innerHTML = "Save Book";

    document.getElementById("book_id").value = "";

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