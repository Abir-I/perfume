#!/usr/bin/env bash
# Run this from the ROOT of your local clone of Abir-I/perfume,
# on the "Abir" branch, with full_backend_and_admin_panel.tar.gz,
# settings_urls_views_patch.patch, and requirements-additions.txt
# in the same folder as this script.
set -e

git checkout Abir
git pull origin Abir

tar -xzf full_backend_and_admin_panel.tar.gz -C .
git apply settings_urls_views_patch.patch

pip install -r requirements-additions.txt

git add -A
git commit -m "Mysha: Sprint 5+6 backend (admin CRUD, image upload, inventory, reviews, env-driven settings, caching, notifications) + admin panel frontend (login/dashboard/products/inventory)"
git push origin Abir

echo "Pushed to Abir."
