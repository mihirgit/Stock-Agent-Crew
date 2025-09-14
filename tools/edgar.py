import requests
import os
from typing import Optional, Dict, List
from xml.etree import ElementTree
import xml.etree.ElementTree as ET
from pathlib import Path


class EdgarTool:
    """
    Fetches SEC 13F filings from EDGAR using the Atom feed search.
    Downloads filings as TXT for display in web app.
    """

    SEARCH_URL = "https://www.sec.gov/cgi-bin/browse-edgar"

    def __init__(self, user_agent: str = "MyStockApp/0.1 (email@example.com)"):
        self.headers = {"User-Agent": user_agent}
        self.download_dir = "downloads/edgar"
        os.makedirs(self.download_dir, exist_ok=True)

    def get_cik(self, ticker: str) -> Optional[str]:
        """Fetch CIK for a given ticker."""
        url = "https://www.sec.gov/files/company_tickers.json"
        resp = requests.get(url, headers=self.headers, timeout=10)
        resp.raise_for_status()
        tickers = resp.json()
        for item in tickers.values():
            if item["ticker"].upper() == ticker.upper():
                return str(int(item["cik_str"]))  # no leading zeros
        return None

    def get_latest_13f(self, ticker: str) -> Optional[Dict]:
        """
        Get latest 13F-HR filing metadata from EDGAR Atom feed.
        Returns dict with keys: ticker, filing_date, accession_number, txt_url
        """
        cik = self.get_cik(ticker)
        if not cik:
            print(f"[EDGAR] CIK not found for {ticker}.")
            return None

        params = {
            "action": "getcompany",
            "CIK": cik,
            "type": "13F-HR",
            "owner": "exclude",
            "count": "10",
            "output": "atom"
        }

        try:
            resp = requests.get(self.SEARCH_URL, headers=self.headers, params=params, timeout=10)
            resp.raise_for_status()
            feed_xml = ElementTree.fromstring(resp.content)
        except Exception as e:
            print(f"[EDGAR] Failed to fetch Atom feed: {e}")
            return None

        # Parse first entry in Atom feed
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entry = feed_xml.find("atom:entry", ns)
        if entry is None:
            print(f"[EDGAR] No 13F-HR filings found for {ticker}.")
            return None

        filing_date = entry.find("atom:updated", ns).text[:10]
        accession_number = entry.find("atom:id", ns).text.split("/")[-1]

        # Primary document URL (usually TXT)
        summary_link = entry.find("atom:link", ns).attrib.get("href")
        if not summary_link:
            print(f"[EDGAR] No document link found for {ticker}.")
            return None

        # The primary TXT document usually ends with ".txt"
        txt_url = summary_link.replace("-index.htm", ".txt")

        return {
            "ticker": ticker,
            "filing_date": filing_date,
            "accession_number": accession_number,
            "txt_url": txt_url
        }

    def download_filing(self, latest_13f: Dict) -> Optional[str]:
        """
        Downloads the 13F TXT filing to downloads/edgar/ and returns the file path.
        """
        if not latest_13f or "txt_url" not in latest_13f:
            print("[EDGAR] No filing available to download.")
            return None

        url = latest_13f["txt_url"]
        ticker = latest_13f["ticker"]
        filing_date = latest_13f["filing_date"]

        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code == 404:
                print(f"[EDGAR] Filing not found (404): {url}")
                return None
            resp.raise_for_status()

            os.makedirs(self.download_dir, exist_ok=True)
            filename = f"{ticker}_{filing_date}.txt"
            filepath = os.path.join(self.download_dir, filename)

            with open(filepath, "wb") as f:
                f.write(resp.content)

            print(f"[EDGAR] Filing downloaded: {filepath}")
            return filepath

        except Exception as e:
            print(f"[EDGAR] Failed to download filing: {e}")
            return None

    def parse_13f_file(self, file_path: Path) -> List[Dict]:
        """
        Parse the 13F INFORMATION TABLE from downloaded .txt/.xml file.
        Returns a list of holdings dictionaries.
        """
        holdings = []
        text = file_path.read_text(encoding="utf-8")

        # Extract the <informationTable> ... </informationTable> block
        start_idx = text.find("<informationTable")
        end_idx = text.find("</informationTable>")
        if start_idx == -1 or end_idx == -1:
            return holdings  # Empty list

        xml_block = text[start_idx:end_idx + len("</informationTable>")]

        try:
            root = ET.fromstring(xml_block)
            ns = {"ns": "http://www.sec.gov/edgar/document/thirteenf/informationtable"}
            for info in root.findall("ns:infoTable", ns):
                holding = {
                    "issuer": info.findtext("ns:nameOfIssuer", default="", namespaces=ns),
                    "class": info.findtext("ns:titleOfClass", default="", namespaces=ns),
                    "cusip": info.findtext("ns:cusip", default="", namespaces=ns),
                    "value": info.findtext("ns:value", default="", namespaces=ns),
                    "shares": info.findtext("ns:shrsOrPrnAmt/ns:sshPrnamt", default="", namespaces=ns),
                    "shares_type": info.findtext("ns:shrsOrPrnAmt/ns:sshPrnamtType", default="", namespaces=ns),
                    "voting_sole": info.findtext("ns:votingAuthority/ns:Sole", default="", namespaces=ns),
                    "voting_shared": info.findtext("ns:votingAuthority/ns:Shared", default="", namespaces=ns),
                    "voting_none": info.findtext("ns:votingAuthority/ns:None", default="", namespaces=ns),
                }
                holdings.append(holding)
        except ET.ParseError:
            return holdings  # Return empty if XML parsing fails

        return holdings