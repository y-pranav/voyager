from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus.flowables import KeepTogether
from io import BytesIO
from typing import Dict, Any
import os

class TripPDFGenerator:
    """Generate PDF reports for trip itineraries"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom PDF styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=20,
            textColor=colors.HexColor('#2563eb'),
            alignment=1  # Center alignment
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceBefore=12,
            spaceAfter=8,
            textColor=colors.HexColor('#1f2937'),
            leftIndent=0
        ))
        
        self.styles.add(ParagraphStyle(
            name='DayHeader',
            parent=self.styles['Heading3'],
            fontSize=12,
            spaceBefore=10,
            spaceAfter=6,
            textColor=colors.HexColor('#059669'),
            leftIndent=0
        ))
        
        self.styles.add(ParagraphStyle(
            name='ActivityText',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceBefore=3,
            spaceAfter=3,
            leftIndent=20
        ))
    
    def generate_pdf(self, itinerary: Dict[str, Any]) -> BytesIO:
        """Generate PDF from itinerary data"""
        try:
            buffer = BytesIO()
            
            # Create PDF document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build content
            story = []
            
            # Title section
            story.extend(self._create_title_section(itinerary))
            
            # Trip overview
            story.extend(self._create_overview_section(itinerary))
            
            # Daily itinerary
            story.extend(self._create_daily_itinerary_section(itinerary))
            
            # Flight information
            story.extend(self._create_flights_section(itinerary))
            
            # Hotels information
            story.extend(self._create_hotels_section(itinerary))
            
            # Cost breakdown
            story.extend(self._create_cost_section(itinerary))
            
            # Recommendations
            story.extend(self._create_recommendations_section(itinerary))
            
            # Build PDF
            doc.build(story)
            buffer.seek(0)
            
            return buffer
            
        except Exception as e:
            print(f"❌ Error generating PDF: {e}")
            raise
    
    def _create_title_section(self, itinerary: Dict[str, Any]) -> list:
        """Create title section"""
        story = []
        
        # Main title
        title = f"AI Trip Planner - {itinerary.get('destination', 'Trip Itinerary')}"
        story.append(Paragraph(title, self.styles['CustomTitle']))
        
        # Trip summary
        summary_data = [
            ["Destination:", itinerary.get('destination', 'N/A')],
            ["Duration:", f"{itinerary.get('total_days', 0)} days"],
            ["Total Cost:", f"₹{itinerary.get('total_cost', 0):,.0f}"],
            ["Currency:", itinerary.get('currency', 'INR')]
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_overview_section(self, itinerary: Dict[str, Any]) -> list:
        """Create trip overview section"""
        story = []
        
        story.append(Paragraph("Trip Overview", self.styles['SectionHeader']))
        
        overview_text = f"""
        This itinerary has been carefully crafted by our AI agents to provide you with an 
        optimal travel experience in {itinerary.get('destination', 'your destination')}. 
        The plan includes {itinerary.get('total_days', 0)} days of activities, accommodations, 
        dining recommendations, and transportation options.
        """
        
        story.append(Paragraph(overview_text, self.styles['Normal']))
        story.append(Spacer(1, 12))
        
        return story
    
    def _create_daily_itinerary_section(self, itinerary: Dict[str, Any]) -> list:
        """Create daily itinerary section"""
        story = []
        
        story.append(Paragraph("Daily Itinerary", self.styles['SectionHeader']))
        
        daily_itinerary = itinerary.get('daily_itinerary', [])
        
        for day in daily_itinerary:
            day_content = []
            
            # Day header
            day_title = f"Day {day.get('day', 'N/A')} - {day.get('date', 'N/A')}"
            day_content.append(Paragraph(day_title, self.styles['DayHeader']))
            
            # Activities
            activities = day.get('activities', [])
            if activities:
                day_content.append(Paragraph("<b>Activities:</b>", self.styles['Normal']))
                for activity in activities:
                    activity_text = f"• <b>{activity.get('time', 'N/A')}</b> - {activity.get('name', 'Activity')}"
                    if activity.get('description'):
                        activity_text += f" - {activity.get('description')}"
                    if activity.get('cost'):
                        activity_text += f" (₹{activity.get('cost', 0):,.0f})"
                    day_content.append(Paragraph(activity_text, self.styles['ActivityText']))
            
            # Meals
            meals = day.get('meals', [])
            if meals:
                day_content.append(Paragraph("<b>Meals:</b>", self.styles['Normal']))
                for meal in meals:
                    meal_text = f"• <b>{meal.get('time', 'N/A')}</b> - {meal.get('name', 'Meal')}"
                    if meal.get('cuisine'):
                        meal_text += f" ({meal.get('cuisine')})"
                    if meal.get('cost'):
                        meal_text += f" - ₹{meal.get('cost', 0):,.0f}"
                    day_content.append(Paragraph(meal_text, self.styles['ActivityText']))
            
            # Accommodation
            accommodation = day.get('accommodation')
            if accommodation and accommodation.get('name'):
                day_content.append(Paragraph("<b>Accommodation:</b>", self.styles['Normal']))
                acc_text = f"• {accommodation.get('name', 'Hotel')}"
                if accommodation.get('location'):
                    acc_text += f" - {accommodation.get('location')}"
                if accommodation.get('price_per_night'):
                    acc_text += f" (₹{accommodation.get('price_per_night', 0):,.0f}/night)"
                day_content.append(Paragraph(acc_text, self.styles['ActivityText']))
            
            # Daily cost
            if day.get('estimated_cost'):
                cost_text = f"<b>Daily Cost: ₹{day.get('estimated_cost', 0):,.0f}</b>"
                day_content.append(Paragraph(cost_text, self.styles['Normal']))
            
            day_content.append(Spacer(1, 10))
            
            # Keep day content together
            story.append(KeepTogether(day_content))
        
        return story
    
    def _create_flights_section(self, itinerary: Dict[str, Any]) -> list:
        """Create flights section"""
        story = []
        
        flights = itinerary.get('flights', {})
        if not flights or not flights.get('options'):
            return story
        
        story.append(Paragraph("Flight Options", self.styles['SectionHeader']))
        
        # Create flight table
        flight_data = [["Airlines", "Duration", "Stops", "Price"]]
        
        for i, flight in enumerate(flights.get('options', [])[:3]):  # Show top 3 flights
            airlines = ', '.join(flight.get('airlines', [])) if isinstance(flight.get('airlines'), list) else 'N/A'
            duration = flight.get('total_duration', 'N/A')
            stops = f"{flight.get('total_stops', 0)} stops" if flight.get('total_stops', 0) > 0 else "Direct"
            price = f"₹{flight.get('price_inr', 0):,.0f}"
            
            flight_data.append([airlines, duration, stops, price])
        
        if len(flight_data) > 1:  # Has data beyond header
            flight_table = Table(flight_data, colWidths=[2*inch, 1.5*inch, 1*inch, 1.5*inch])
            flight_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#d1d5db')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            
            story.append(flight_table)
            story.append(Spacer(1, 12))
        
        return story
    
    def _create_hotels_section(self, itinerary: Dict[str, Any]) -> list:
        """Create hotels section"""
        story = []
        
        hotels = itinerary.get('hotels', {})
        if not hotels or not hotels.get('options'):
            return story
        
        story.append(Paragraph("Hotel Options", self.styles['SectionHeader']))
        
        # Create hotel table
        hotel_data = [["Hotel Name", "Rating", "Price/Night", "Total Price"]]
        
        for i, hotel in enumerate(hotels.get('options', [])[:3]):  # Show top 3 hotels
            name = hotel.get('name', 'N/A')[:30] + '...' if len(hotel.get('name', '')) > 30 else hotel.get('name', 'N/A')
            rating = f"{hotel.get('rating', 0):.1f}/5" if hotel.get('rating') else 'N/A'
            price_per_night = f"₹{hotel.get('price_per_night', 0):,.0f}"
            total_price = f"₹{hotel.get('total_price', 0):,.0f}"
            
            hotel_data.append([name, rating, price_per_night, total_price])
        
        if len(hotel_data) > 1:  # Has data beyond header
            hotel_table = Table(hotel_data, colWidths=[2.5*inch, 1*inch, 1.2*inch, 1.3*inch])
            hotel_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),  # Center align numbers
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),     # Left align hotel names
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#d1d5db')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            
            story.append(hotel_table)
            story.append(Spacer(1, 12))
        
        return story
    
    def _create_cost_section(self, itinerary: Dict[str, Any]) -> list:
        """Create cost breakdown section"""
        story = []
        
        story.append(Paragraph("Cost Breakdown", self.styles['SectionHeader']))
        
        # Calculate costs
        total_cost = itinerary.get('total_cost', 0)
        flights_cost = 0
        hotels_cost = 0
        
        # Get flight cost
        flights = itinerary.get('flights', {})
        if flights.get('options'):
            flights_cost = flights['options'][0].get('price_inr', total_cost * 0.3)
        else:
            flights_cost = total_cost * 0.3
        
        # Get hotel cost
        hotels = itinerary.get('hotels', {})
        if hotels.get('options'):
            hotels_cost = hotels['options'][0].get('total_price', total_cost * 0.4)
        else:
            hotels_cost = total_cost * 0.4
        
        # Calculate other costs
        activities_cost = total_cost * 0.15
        meals_cost = total_cost * 0.15
        
        cost_data = [
            ["Category", "Amount", "Percentage"],
            ["Flights", f"₹{flights_cost:,.0f}", f"{(flights_cost/total_cost)*100:.1f}%"],
            ["Hotels", f"₹{hotels_cost:,.0f}", f"{(hotels_cost/total_cost)*100:.1f}%"],
            ["Activities", f"₹{activities_cost:,.0f}", f"{(activities_cost/total_cost)*100:.1f}%"],
            ["Meals", f"₹{meals_cost:,.0f}", f"{(meals_cost/total_cost)*100:.1f}%"],
            ["TOTAL", f"₹{total_cost:,.0f}", "100.0%"]
        ]
        
        cost_table = Table(cost_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
        cost_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#d1d5db')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(cost_table)
        story.append(Spacer(1, 12))
        
        return story
    
    def _create_recommendations_section(self, itinerary: Dict[str, Any]) -> list:
        """Create recommendations section"""
        story = []
        
        recommendations = itinerary.get('recommendations', [])
        if not recommendations:
            return story
        
        story.append(Paragraph("AI Recommendations", self.styles['SectionHeader']))
        
        for i, recommendation in enumerate(recommendations[:5], 1):  # Show top 5
            rec_text = f"{i}. {recommendation}"
            story.append(Paragraph(rec_text, self.styles['Normal']))
        
        story.append(Spacer(1, 12))
        
        # Footer
        footer_text = """
        <br/><br/>
        <i>This itinerary was generated by AI Trip Planner. 
        Prices and availability are subject to change. 
        Please verify all bookings before finalizing your travel plans.</i>
        """
        story.append(Paragraph(footer_text, self.styles['Normal']))
        
        return story
