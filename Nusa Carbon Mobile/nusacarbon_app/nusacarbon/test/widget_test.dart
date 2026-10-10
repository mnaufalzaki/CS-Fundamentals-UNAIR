import 'package:flutter_test/flutter_test.dart';
import 'package:nusacarbon/main.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  testWidgets('NusaCarbon role selection screen loads', (
    WidgetTester tester,
  ) async {
    SharedPreferences.setMockInitialValues({});

    await tester.pumpWidget(const NusaCarbonApp());
    await tester.pump();

    expect(find.text('NusaCarbon'), findsOneWidget);
    expect(find.text('Buyer'), findsOneWidget);
    expect(find.text('Project Owner'), findsOneWidget);
    expect(find.text('Verifier'), findsOneWidget);
    expect(find.text('Admin'), findsOneWidget);
  });
}
