import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:my_app/src/app.dart';

void main() {
  testWidgets('Home screen renders title', (WidgetTester tester) async {
    await tester.pumpWidget(const ProviderScope(child: MyApp()));
    await tester.pumpAndSettle();

    expect(find.text('Welcome to my_app'), findsOneWidget);
  });
}
