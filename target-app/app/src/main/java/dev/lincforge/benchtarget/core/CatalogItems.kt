package dev.lincforge.benchtarget.core

/** SPEC.md § Screens 2: "Item 001" … "Item 100", three-digit zero-padded. */
object CatalogItems {
    val all: List<String> = (1..100).map { "Item %03d".format(it) }
}
