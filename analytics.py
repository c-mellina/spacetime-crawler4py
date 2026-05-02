from collections import Counter
from urllib.parse import urlparse

unique_pages = set()
word_counter = Counter()
longest_page = ("", 0)
subdomains = {}

def add_page(url, all_words, filtered_words):
    global longest_page
    
    #skip if already looked thru
    if url in unique_pages:
        return
    unique_pages.add(url)

    #check if this is the longest page seen
    if len(all_words) > longest_page[1]:
        longest_page = (url, len(all_words))

    word_counter.update(filtered_words)

    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    #only count subdomains within uci.edu (q4!)
    if domain.endswith(".uci.edu"):
        if domain not in subdomains:
            subdomains[domain] = 0
        subdomains[domain] += 1

def write_report(filename="report.txt"):
    with open(filename, "w") as f:
        f.write("Unique pages found: " + str(len(unique_pages)) + "\n\n")

        #longest page info
        f.write("Longest page:\n")
        f.write(longest_page[0] + "\n")
        f.write("Word count: " + str(longest_page[1]) + "\n\n")

        #top 50 most common words
        f.write("Top 50 words:\n")
        for word, count in word_counter.most_common(50):
            f.write(word + ", " + str(count) + "\n")

        #list of subdomains (in alphabetic order) + how many pages!
        f.write("\nSubdomains: " + str(len(subdomains)) + " total\n")
        for domain in sorted(subdomains):
            f.write(domain + ", " + str(subdomains[domain]) + "\n")