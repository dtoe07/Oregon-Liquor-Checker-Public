# Oregon-Liquor-Checker

Setup Action secrets for the script to fetch in order to login to gmail service:

- **LOGIN_EMAIL**
- **ACCESS_TOKEN**
- **MAPS_TOKEN**

Setup repo variables in git action variables:

- **TEST_EMAIL_LIST**

Commend out the creating map section within method `parse_multiple_stores` if you want to skip setting up a new repo to save them.

```
# Create a map with the store addresses found
    if store_in_stock:
        # Use product code to name the map file
        print(f"📍 Creating map for item: {item_name}")
        create_map(store_in_stock, f"{item_number}_map.html")
        # Append the map URL to the global list for inclusion in the email
        map_urls.append(
            (
                item_name,
                f"https://dtoe07.github.io/map-hosting/{zip_code}/{item_number}_map.html",
            )
        )
```

Also commend out the last section in the action yml file to not dealing with maps:

```
# Deploy generated maps to public GitHub repo (your-github-id/map-hosting) with subfolder for different ZIP codes
      - name: Deploy to public maps repo
        uses: peaceiris/actions-gh-pages@v3
        with:
          personal_token: ${{ secrets.MAPS_TOKEN }}
          external_repository: your-github-id/map-hosting
          publish_branch: gh-pages
          publish_dir: ./maps
          destination_dir: ${{ env.ZIP_CODE }} # <-- this creates a subfolder for that ZIP
          keep_files: true # keeps old ZIP folders
```

Setup a public git pages to store the maps. If not just comment out the creating map section from the code.

Example email output:
![email top](email_top.png)

Here is how the maps at the bottom looks like:

![email top](email_bottom.png)

Here is how the maps display:
![email top](maps.png)
