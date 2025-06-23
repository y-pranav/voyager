from langchain.tools import BaseTool
from typing import Optional, Type, Dict, Any
from pydantic import BaseModel, Field

class CurrencyConverterInput(BaseModel):
    """Input for currency converter tool"""
    amount: float = Field(description="Amount to convert")
    from_currency: str = Field("INR", description="Source currency code (default: INR)")
    to_currency: str = Field("USD", description="Target currency code")

class CurrencyConverterTool(BaseTool):
    """Tool for converting currencies and budget calculations"""
    
    name = "currency_converter"
    description = """Convert currencies and calculate budget equivalents.
    Use this tool to help users understand costs in different currencies
    and to convert budget amounts for international planning."""
    args_schema: Type[BaseModel] = CurrencyConverterInput
    
    def _run(
        self,
        amount: float,
        from_currency: str = "INR",
        to_currency: str = "USD",
        **kwargs: Any,
    ) -> str:
        """Execute the currency conversion"""
        
        # Mock exchange rates - replace with real currency API calls
        # Base rates against INR (as of a typical rate)
        exchange_rates = {
            "USD": 83.0,    # 1 USD = 83 INR
            "EUR": 90.0,    # 1 EUR = 90 INR
            "GBP": 105.0,   # 1 GBP = 105 INR
            "JPY": 0.56,    # 1 JPY = 0.56 INR
            "SGD": 62.0,    # 1 SGD = 62 INR
            "AUD": 55.0,    # 1 AUD = 55 INR
            "CAD": 61.0,    # 1 CAD = 61 INR
            "CHF": 92.0,    # 1 CHF = 92 INR
            "CNY": 11.5,    # 1 CNY = 11.5 INR
            "THB": 2.35,    # 1 THB = 2.35 INR
            "MYR": 18.0,    # 1 MYR = 18 INR
            "INR": 1.0      # Base currency
        }
        
        # Normalize currency codes
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        # Validate currencies
        if from_currency not in exchange_rates or to_currency not in exchange_rates:
            return f"Error: Unsupported currency. Supported currencies: {', '.join(exchange_rates.keys())}"
        
        # Convert to INR first, then to target currency
        if from_currency == "INR":
            inr_amount = amount
        else:
            inr_amount = amount * exchange_rates[from_currency]
        
        if to_currency == "INR":
            converted_amount = inr_amount
        else:
            converted_amount = inr_amount / exchange_rates[to_currency]
        
        # Calculate some useful budget breakdowns
        budget_breakdown = self._get_budget_breakdown(converted_amount, to_currency)
        
        # Get currency symbol
        currency_symbols = {
            "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥",
            "SGD": "S$", "AUD": "A$", "CAD": "C$", "CHF": "CHF",
            "CNY": "¥", "THB": "฿", "MYR": "RM", "INR": "₹"
        }
        
        from_symbol = currency_symbols.get(from_currency, from_currency)
        to_symbol = currency_symbols.get(to_currency, to_currency)
        
        return f"""Currency Conversion:

CONVERSION RESULT:
{from_symbol}{amount:,.2f} {from_currency} = {to_symbol}{converted_amount:,.2f} {to_currency}

EXCHANGE RATE:
1 {from_currency} = {(exchange_rates[to_currency] / exchange_rates[from_currency]):.4f} {to_currency}
1 {to_currency} = {(exchange_rates[from_currency] / exchange_rates[to_currency]):.4f} {from_currency}

{budget_breakdown}

MONEY TIPS:
• Exchange rates fluctuate daily - check current rates before travel
• Consider using cards with no foreign transaction fees
• Keep some local currency for small purchases
• ATMs often offer better rates than exchange counters
• Inform your bank about travel plans to avoid card blocks
"""

    def _get_budget_breakdown(self, amount: float, currency: str) -> str:
        """Generate budget breakdown suggestions"""
        if currency == "INR":
            # Budget breakdown for INR amounts
            daily_budget = amount / 7  # Assume 7-day trip
            breakdown = {
                "Accommodation (40%)": amount * 0.4,
                "Food & Dining (25%)": amount * 0.25,
                "Transportation (20%)": amount * 0.2,
                "Activities & Tours (10%)": amount * 0.1,
                "Shopping & Misc (5%)": amount * 0.05
            }
            
            result = f"\nBUDGET BREAKDOWN (₹{amount:,.0f} total):\n"
            for category, cost in breakdown.items():
                result += f"• {category}: ₹{cost:,.0f}\n"
            result += f"\nDaily Budget: ₹{daily_budget:,.0f} per day"
            
        else:
            # For other currencies, provide general guidance
            currency_symbols = {
                "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥",
                "SGD": "S$", "AUD": "A$", "CAD": "C$", "CHF": "CHF",
                "CNY": "¥", "THB": "฿", "MYR": "RM"
            }
            symbol = currency_symbols.get(currency, currency)
            
            daily_budget = amount / 7
            result = f"\nBUDGET GUIDANCE:\n"
            result += f"• Total Budget: {symbol}{amount:,.2f}\n"
            result += f"• Daily Budget: {symbol}{daily_budget:,.2f} per day\n"
            result += f"• This budget level is typically suitable for mid-range travel"
        
        return result

    async def _arun(
        self,
        amount: float,
        from_currency: str = "INR",
        to_currency: str = "USD",
        **kwargs: Any,
    ) -> str:
        """Async version of the currency converter"""
        return self._run(amount, from_currency, to_currency, **kwargs)
