---
company: all_three
area: cross_platform_comparison
subtopic: gst_and_tcs_handling
source_tier: synthesized_from_public_sources
---

# Cross-Platform Comparison: GST & TCS Handling (Flipkart vs Amazon India vs Meesho)

> Synthesized comparison drawing on the shared GST documents and per-company onboarding guides in this corpus. Written in prose rather than table format so it extracts cleanly through plain-text PDF parsing.

## What's Identical Across All Three, By Law
The TCS rate — 0.5% CGST plus 0.5% SGST on intra-state sales, or 1% IGST on inter-state sales — comes from Section 52 of the CGST Act and applies uniformly to Flipkart, Amazon India, and Meesho alike. This is federal law, not a platform choice, so a seller cannot find a "better TCS rate" by choosing one platform over another. Likewise, none of the three platforms can offer a turnover-based GST exemption to their sellers: Section 24 of the CGST Act overrides the standard ₹40 lakh exemption threshold for anyone selling through an e-commerce operator, on all three platforms equally. Each platform separately files Form GSTR-8 monthly, reporting the TCS it collected on the seller's behalf, and this filing auto-populates the seller's GSTR-2A identically regardless of which platform generated the sale.

## Where the Platforms Actually Differ
The differences between Flipkart, Amazon, and Meesho on GST are operational, not legal. Flipkart requires a valid GSTIN at Seller Hub registration for every product category, with no documented exception. Amazon India similarly requires GSTIN verification before a seller account can be activated at all — Amazon will not let an account go live without it. Meesho is the one platform with a genuine accommodation for very small sellers: below ₹40 lakh in annual turnover, Meesho accepts an "Enrollment ID" in place of a full GSTIN. This doesn't change what tax is legally owed — a seller below the mandatory-registration threshold under ordinary GST law still isn't required to register regardless of platform — but it does change what a very small Meesho seller needs to submit at signup compared to what Flipkart or Amazon would require of an equivalent seller.

Where each platform surfaces the TCS certificate also differs: Flipkart shows it within the Seller Hub's payment/TCS section, Amazon shows it under Seller Central's Settings > Account Info > Tax Information, and Meesho shows it within the Supplier Panel. These are dashboard/UX differences, not differences in the underlying tax treatment.

## Practical Implication for a Seller on All Three Platforms
A seller registered on Flipkart, Amazon, and Meesho simultaneously uses the exact same GSTIN across all three — GST registration is tied to the business, not to any individual platform. That seller must still separately upload or link the GSTIN within each platform's own seller dashboard, and will see three separate TCS credit entries in their monthly GSTR-2A — one corresponding to sales made through each platform — even though all three trace back to the same underlying GST registration and the same Section 52 obligation.

## Sources
This comparison is derived entirely from the individual documents already in this corpus (gst_tcs_official_rules, gst_einvoice_advisory, flipkart_seller_operations_guide, amazon_seller_operations_guide, meesho_seller_operations_guide) — no new external sources beyond those already cited there.
